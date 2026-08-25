# Implementation — llm_client

## Traceability
- R1 → `test_complete_happy_path`
- R2 → `test_missing_api_key_raises_before_network`
- R3 → `test_api_error_includes_status_and_detail`
- R4 → `test_invalid_json_raises_parse_error`, `test_non_object_json_raises_parse_error`
- R5 → code review: no bare `except:`; every error does `raise ... from exc` with context
- R6 → all tests use an injected `FakeTransport` (zero network)

## Tasks checklist (specs/llm_client/tasks.md)
- [x] T1 — LLMError, LLMAuthError, LLMParseError
- [x] T2 — Transport protocol + UrllibTransport with timeout (120 s)
- [x] T3 — GroqClient.complete() with auth pre-check and non-2xx handling
- [x] T4 — GroqClient.complete_json() with a fragment of the response in the error
- [x] T5–T8 — tests/test_llm_client.py
- [x] T9 — `uv run pytest`: 27 passed (full suite)

## Notes / deviations
- No deviation from the approved spec. `HTTPError` is treated as a response
  (returns status + body) so that `complete()` centralizes the error with
  detail; `URLError` (network down) is wrapped in `LLMError` with the cause.
