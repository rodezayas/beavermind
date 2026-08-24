"""LLM clients for the scoring engine (Groq and Anthropic).

Thin, dependency-free HTTP clients with an injectable transport so tests run
without network access. Both providers expose the same small interface
(`complete` / `complete_json`); `make_llm_client` picks one from settings.
Every failure path raises an explicit error carrying context; nothing is
swallowed.
"""

import json
import time
from typing import Protocol

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.config import Settings

#: Groq chat-completions endpoint
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

#: Anthropic Messages endpoint
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

#: Anthropic API version header value (current stable contract)
ANTHROPIC_VERSION = "2023-06-01"

#: Default model used for scoring. `groq/compound-mini` has a 70,000 TPM free
#: tier limit (~9x gpt-oss-120b's 8k), which long transcripts need; override
#: per environment with GROQ_MODEL.
GROQ_MODEL = "groq/compound-mini"

#: Default Anthropic model for scoring; override with ANTHROPIC_MODEL
ANTHROPIC_MODEL = "claude-sonnet-5"

#: Seconds before a request is aborted so a run never hangs in `scoring`
REQUEST_TIMEOUT_SECONDS = 120

#: Seconds to wait before the single retry of a truncated/invalid JSON reply.
#: Rate-limit variance can cut a completion mid-JSON; one retry after the
#: per-minute window rolls over recovers most of these cases.
JSON_RETRY_DELAY_SECONDS = 15.0


class LLMError(RuntimeError):
    """Base error for LLM calls; carries HTTP status when available."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class LLMAuthError(LLMError):
    """Raised when the provider API key is missing before any network call."""


class LLMParseError(LLMError):
    """Raised when the model reply cannot be parsed as JSON."""


class Transport(Protocol):
    """Minimal HTTP transport abstraction (injectable for tests)."""

    def post(self, url: str, headers: dict[str, str], payload: dict) -> tuple[int, str]:
        """POST `payload` as JSON and return (http_status, body_text)."""
        ...  # pragma: no cover


class UrllibTransport:
    """Default transport built on the standard library."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT_SECONDS) -> None:
        """Create the transport.

        Args:
            timeout: Seconds before a request is aborted. Slower reasoning
                models (e.g. Opus on very long transcripts) need more time.
        """
        self._timeout = timeout

    def post(self, url: str, headers: dict[str, str], payload: dict) -> tuple[int, str]:
        """POST `payload` as JSON and return (http_status, body_text).

        Raises:
            LLMError: On connection failures, with the underlying reason.
        """
        request = Request(  # noqa: S310 - fixed https URL
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            # HTTPError is also a response: surface status and body.
            body = exc.read().decode("utf-8", errors="replace")
            return exc.code, body
        except URLError as exc:
            raise LLMError(f"LLM API connection failed: {exc.reason}") from exc


class BaseLLMClient:
    """Shared behavior for provider clients: JSON parsing with one retry."""

    def complete(self, prompt: str) -> str:
        """Send `prompt` to the model and return the reply text."""
        raise NotImplementedError  # pragma: no cover

    def complete_json(self, prompt: str) -> dict:
        """Like `complete`, but parses the reply as a JSON object.

        A reply that is not valid JSON is retried once (rate-limit variance
        can truncate a completion mid-JSON); a second failure raises.

        Raises:
            LLMParseError: If the reply is not valid JSON after the retry;
                includes a fragment of the offending reply.
        """
        try:
            return self._complete_json_once(prompt)
        except LLMParseError:
            time.sleep(JSON_RETRY_DELAY_SECONDS)
            return self._complete_json_once(prompt)

    def _complete_json_once(self, prompt: str) -> dict:
        """Single attempt of `complete_json` without retry logic."""
        reply = self.complete(prompt)
        try:
            parsed = json.loads(reply)
        except json.JSONDecodeError as exc:
            raise LLMParseError(
                f"Model reply is not valid JSON: {reply[:300]}"
            ) from exc
        if not isinstance(parsed, dict):
            raise LLMParseError(
                f"Model reply is not a JSON object: {reply[:300]}"
            )
        return parsed


class GroqClient(BaseLLMClient):
    """Calls Groq's chat-completions API (default: groq/compound-mini)."""

    def __init__(self, settings: Settings, transport: Transport | None = None) -> None:
        """Create a client.

        Args:
            settings: Application settings; must contain `groq_api_key`.
            transport: HTTP transport; defaults to `UrllibTransport`.
        """
        if not settings.groq_api_key:
            raise LLMAuthError(
                "GROQ_API_KEY is missing: set it in the environment before "
                "creating a GroqClient"
            )
        self._api_key = settings.groq_api_key  # never logged
        self._model = settings.groq_model  # configurable via GROQ_MODEL
        self._transport = transport if transport is not None else UrllibTransport()

    def complete(self, prompt: str) -> str:
        """Send `prompt` to the model and return the reply text.

        Raises:
            LLMError: On non-2xx responses or connection failures; includes
                the HTTP status and response detail.
        """
        status, body = self._transport.post(
            GROQ_API_URL,
            headers=self._headers(),
            payload=self._payload(prompt),
        )
        if status >= 300:
            raise LLMError(
                f"Groq API error (HTTP {status}): {body[:500]}", status=status
            )
        try:
            reply = json.loads(body)["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise LLMError(
                f"Unexpected Groq response shape: {body[:500]}"
            ) from exc
        if not isinstance(reply, str):
            raise LLMError(f"Unexpected Groq response shape: {body[:500]}")
        return reply

    def _headers(self) -> dict[str, str]:
        """Build request headers (authorization + JSON content type).

        A custom User-Agent is required: Groq sits behind Cloudflare, which
        rejects the default `Python-urllib/x.y` signature with HTTP 403
        (error 1010).
        """
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": "scoring-system/1.0",
        }

    def _payload(self, prompt: str) -> dict:
        """Build the chat-completions request body."""
        return {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }


class AnthropicClient(BaseLLMClient):
    """Calls Anthropic's Messages API (default: claude-sonnet-5)."""

    #: Anthropic requires an explicit output ceiling. Opus-class models are
    #: verbose scorers (12 dimensions with quoted evidence); 32k leaves ample
    #: room while still bounding runaway completions.
    MAX_OUTPUT_TOKENS = 32000

    #: Opus scoring a very long transcript can take several minutes; the
    #: default 120s request timeout is not enough.
    TIMEOUT_SECONDS = 600.0

    def __init__(self, settings: Settings, transport: Transport | None = None) -> None:
        """Create a client.

        Args:
            settings: Application settings; must contain `anthropic_api_key`.
            transport: HTTP transport; defaults to `UrllibTransport` with the
                extended Opus timeout.
        """
        if not settings.anthropic_api_key:
            raise LLMAuthError(
                "ANTHROPIC_API_KEY is missing: set it in the environment "
                "before creating an AnthropicClient (or set LLM_PROVIDER=groq)"
            )
        self._api_key = settings.anthropic_api_key  # never logged
        self._model = settings.anthropic_model  # configurable via ANTHROPIC_MODEL
        self._transport = transport if transport is not None else UrllibTransport(
            timeout=self.TIMEOUT_SECONDS
        )

    def complete(self, prompt: str) -> str:
        """Send `prompt` to the model and return the reply text.

        Raises:
            LLMError: On non-2xx responses or connection failures; includes
                the HTTP status and response detail.
        """
        status, body = self._transport.post(
            ANTHROPIC_API_URL,
            headers=self._headers(),
            payload=self._payload(prompt),
        )
        if status >= 300:
            raise LLMError(
                f"Anthropic API error (HTTP {status}): {body[:500]}", status=status
            )
        try:
            blocks = json.loads(body)["content"]
            reply = next(b["text"] for b in blocks if b.get("type") == "text")
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, StopIteration) as exc:
            raise LLMError(
                f"Unexpected Anthropic response shape: {body[:500]}"
            ) from exc
        if not isinstance(reply, str):
            raise LLMError(f"Unexpected Anthropic response shape: {body[:500]}")
        return reply

    def _headers(self) -> dict[str, str]:
        """Build request headers per the Anthropic Messages contract."""
        return {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "scoring-system/1.0",
        }

    def _payload(self, prompt: str) -> dict:
        """Build the Messages request body.

        `max_tokens` is mandatory and `temperature` is deprecated on current
        Opus-class models, so neither is sent beyond what the API requires.
        """
        return {
            "model": self._model,
            "max_tokens": self.MAX_OUTPUT_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }


def make_llm_client(settings: Settings, transport: Transport | None = None) -> BaseLLMClient:
    """Build the provider client selected by `settings.llm_provider`.

    Args:
        settings: Application settings (`LLM_PROVIDER`: groq | anthropic).
        transport: Optional injected HTTP transport for tests.

    Returns:
        The configured client instance for the selected provider.

    Raises:
        ConfigError: If the provider name is unknown.
    """
    if settings.llm_provider == "groq":
        return GroqClient(settings, transport)
    if settings.llm_provider == "anthropic":
        return AnthropicClient(settings, transport)
    raise ValueError(
        f"Unknown llm_provider {settings.llm_provider!r}: expected groq or anthropic"
    )


__all__ = [
    "ANTHROPIC_API_URL",
    "ANTHROPIC_MODEL",
    "GROQ_API_URL",
    "GROQ_MODEL",
    "AnthropicClient",
    "BaseLLMClient",
    "GroqClient",
    "LLMAuthError",
    "LLMError",
    "LLMParseError",
    "Transport",
    "UrllibTransport",
    "make_llm_client",
]
