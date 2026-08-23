"""Tests for src/llm_client.py (feature: llm_client).

All tests use an injected FakeTransport; no real network calls are made.
"""

import json

import pytest

from src.config import Settings
from src.llm_client import (
    GROQ_MODEL,
    GroqClient,
    LLMAuthError,
    LLMError,
    LLMParseError,
)

VALID_SETTINGS = Settings(
    groq_api_key="test-key",
    supabase_project_id="p",
    supabase_api_key="a",
    supabase_secret_key="s",
    database="db",
)


class FakeTransport:
    """Transport stub returning a canned (status, body) response."""

    def __init__(self, status: int = 200, reply: str | None = None) -> None:
        self.status = status
        self.reply = reply if reply is not None else json.dumps(
            {"choices": [{"message": {"content": "{\"ok\": true}"}}]}
        )
        self.calls: list[dict] = []  # records (url, headers, payload)

    def post(self, url: str, headers: dict[str, str], payload: dict) -> tuple[int, str]:
        self.calls.append({"url": url, "headers": headers, "payload": payload})
        if self.status >= 300:
            return self.status, '{"error": {"message": "quota exceeded"}}'
        return self.status, self.reply


def _client(transport: FakeTransport) -> GroqClient:
    return GroqClient(settings=VALID_SETTINGS, transport=transport)


# --- R2: auth pre-check -----------------------------------------------------


def test_missing_api_key_raises_before_network():
    """R2: missing key raises LLMAuthError without touching the transport."""
    missing = VALID_SETTINGS.model_copy(update={"groq_api_key": ""})
    transport = FakeTransport()
    with pytest.raises(LLMAuthError, match="GROQ_API_KEY"):
        GroqClient(settings=missing, transport=transport)
    assert transport.calls == []  # no network call attempted


# --- R1 / R6: happy path ----------------------------------------------------


def test_complete_happy_path():
    """R1, R6: complete() returns the reply and sends the expected request."""
    transport = FakeTransport(
        reply=json.dumps(
            {"choices": [{"message": {"content": "scored!"}}]}
        )
    )
    reply = _client(transport).complete("score this transcript")
    assert reply == "scored!"
    call = transport.calls[0]
    assert call["payload"]["model"] == GROQ_MODEL
    assert call["payload"]["messages"][0]["content"] == "score this transcript"
    assert call["headers"]["Authorization"] == "Bearer test-key"


def test_complete_json_happy_path():
    """R6: complete_json() parses a valid JSON reply into a dict."""
    transport = FakeTransport(
        reply=json.dumps(
            {"choices": [{"message": {"content": '{"total": 88}'}}]}
        )
    )
    assert _client(transport).complete_json("score") == {"total": 88}


# --- R3: API errors ---------------------------------------------------------


def test_api_error_includes_status_and_detail():
    """R3: non-2xx responses raise LLMError with status and body detail."""
    transport = FakeTransport(status=429)
    with pytest.raises(LLMError) as exc:
        _client(transport).complete("prompt")
    assert exc.value.status == 429
    assert "quota exceeded" in str(exc.value)


# --- R4: JSON parse errors --------------------------------------------------


def test_invalid_json_raises_parse_error():
    """R4: a non-JSON reply raises LLMParseError including a reply fragment."""
    raw = "sorry, here is your score: total=88, great call!"
    wrapped = json.dumps({"choices": [{"message": {"content": raw}}]})
    transport = FakeTransport(reply=wrapped)
    with pytest.raises(LLMParseError) as exc:
        _client(transport).complete_json("score")
    assert "total=88" in str(exc.value)


def test_non_object_json_raises_parse_error():
    """R4: a JSON array reply is rejected (an object is required)."""
    wrapped = json.dumps({"choices": [{"message": {"content": "[1, 2, 3]"}}]})
    with pytest.raises(LLMParseError, match="not a JSON object"):
        _client(FakeTransport(reply=wrapped)).complete_json("score")
