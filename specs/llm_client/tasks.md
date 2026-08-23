# Tasks — llm_client

- [ ] T1 — Create `src/llm_client.py` with `LLMError`, `LLMAuthError`, `LLMParseError`. Covers: R2, R3, R4.
- [ ] T2 — Implement `Transport` protocol and default `urllib` transport with explicit timeout. Covers: R1, R6.
- [ ] T3 — Implement `GroqClient.complete(prompt)` with auth pre-check and non-2xx handling. Covers: R1, R2, R3.
- [ ] T4 — Implement `GroqClient.complete_json(prompt)` with JSON parse error including reply fragment. Covers: R4.
- [ ] T5 — Write `tests/test_llm_client.py::test_missing_api_key_raises_before_network` (FakeTransport must not be called). Covers: R2.
- [ ] T6 — Write `tests/test_llm_client.py::test_api_error_includes_status_and_detail`. Covers: R3, R5.
- [ ] T7 — Write `tests/test_llm_client.py::test_invalid_json_raises_parse_error`. Covers: R4.
- [ ] T8 — Write `tests/test_llm_client.py::test_complete_happy_path` with `FakeTransport`. Covers: R1, R6.
- [ ] T9 — Run `uv run pytest`; suite green. Covers: R1–R6.
