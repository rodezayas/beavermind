# Design — llm_client

> How feature 3 is built. Decisions made before writing code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/llm_client.py` | create | `GroqClient`, `LLMError`, `LLMAuthError`, `LLMParseError` |
| `tests/test_llm_client.py` | create | R2–R6 coverage with a transport stub |

## New signatures

```python
# src/llm_client.py
class LLMError(RuntimeError): ...        # status + detail (R3)
class LLMAuthError(LLMError): ...        # missing GROQ_API_KEY (R2)
class LLMParseError(LLMError): ...       # non-JSON response (R4)

class GroqClient:
    MODEL = "openai/gpt-oss-120b"
    def __init__(self, settings: Settings, transport: Transport | None = None): ...
    def complete(self, prompt: str) -> str: ...
    def complete_json(self, prompt: str) -> dict: ...  # parses JSON, R4
```

`Transport` is a protocol with `post(url, headers, payload) -> (status, body)`;
by default `urllib.request` (stdlib) is used, injectable in tests (R6).

## Decisions
- **Direct HTTP with `urllib` (stdlib)** instead of the `groq` SDK: the surface
  we use is a single chat/completions endpoint; the SDK adds a dependency
  and its own exception layer that would duplicate ours. The base URL and
  model remain constants.
- **`complete_json` separate from `complete`**: scoring (feature 5) needs
  structured JSON; keeping both explicit avoids implicit parsing.
- **Explicit timeout** in the default transport so a run never gets stuck
  in `scoring`.

## Alternative discarded
- Official `groq` SDK: discarded because we only use 1 endpoint; with `urllib` +
  the `Transport` protocol, tests need neither network nor SDK mocks, and we avoid
  one more dependency in `pyproject.toml` (rule: every package earns its place).

## Traceability preview
- R2 → `test_missing_api_key_raises_before_network`
- R3 → `test_api_error_includes_status_and_detail`
- R4 → `test_invalid_json_raises_parse_error`
- R5 → code review (no bare `except:`) + error tests
- R6 → all tests use an injected `FakeTransport`
