"""Client for the Groq LLM API (OpenAI GPT-OSS 120B).

Thin, dependency-free HTTP client with an injectable transport so tests run
without network access. Every failure path raises an explicit error carrying
context; nothing is swallowed.
"""

import json
import time
from typing import Protocol

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.config import Settings

#: Groq chat-completions endpoint
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

#: Model used for all scoring calls
GROQ_MODEL = "openai/gpt-oss-120b"

#: Seconds before a request is aborted so a run never hangs in `scoring`
REQUEST_TIMEOUT_SECONDS = 120

#: Seconds to wait before the single retry of a truncated/invalid JSON reply.
#: On the free tier, TPM variance can cut a completion mid-JSON; one retry
#: after the per-minute window rolls over recovers most of these cases.
JSON_RETRY_DELAY_SECONDS = 15.0


class LLMError(RuntimeError):
    """Base error for LLM calls; carries HTTP status when available."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class LLMAuthError(LLMError):
    """Raised when GROQ_API_KEY is missing before any network call."""


class LLMParseError(LLMError):
    """Raised when the model reply cannot be parsed as JSON."""


class Transport(Protocol):
    """Minimal HTTP transport abstraction (injectable for tests)."""

    def post(self, url: str, headers: dict[str, str], payload: dict) -> tuple[int, str]:
        """POST `payload` as JSON and return (http_status, body_text)."""
        ...  # pragma: no cover


class UrllibTransport:
    """Default transport built on the standard library."""

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
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            # HTTPError is also a response: surface status and body.
            body = exc.read().decode("utf-8", errors="replace")
            return exc.code, body
        except URLError as exc:
            raise LLMError(f"Groq API connection failed: {exc.reason}") from exc


class GroqClient:
    """Calls Groq's chat-completions API with the GPT-OSS 120B model."""

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

    def complete_json(self, prompt: str) -> dict:
        """Like `complete`, but parses the reply as a JSON object.

        A reply that is not valid JSON is retried once (TPM variance on the
        free tier can truncate a completion mid-JSON); a second failure raises.

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

    @staticmethod
    def _payload(prompt: str) -> dict:
        """Build the chat-completions request body."""
        return {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }


__all__ = [
    "GROQ_API_URL",
    "GROQ_MODEL",
    "GroqClient",
    "LLMAuthError",
    "LLMError",
    "LLMParseError",
    "Transport",
    "UrllibTransport",
]
