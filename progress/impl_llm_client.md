# Implementation — llm_client

## Traceability
- R1 → `test_complete_happy_path`
- R2 → `test_missing_api_key_raises_before_network`
- R3 → `test_api_error_includes_status_and_detail`
- R4 → `test_invalid_json_raises_parse_error`, `test_non_object_json_raises_parse_error`
- R5 → revisión de código: no hay `except:` desnudo; cada error hace `raise ... from exc` con contexto
- R6 → todos los tests usan `FakeTransport` inyectado (cero red)

## Tasks checklist (specs/llm_client/tasks.md)
- [x] T1 — LLMError, LLMAuthError, LLMParseError
- [x] T2 — Transport protocol + UrllibTransport con timeout (120 s)
- [x] T3 — GroqClient.complete() con pre-check de auth y manejo non-2xx
- [x] T4 — GroqClient.complete_json() con fragmento de la respuesta en el error
- [x] T5–T8 — tests/test_llm_client.py
- [x] T9 — `uv run pytest`: 27 passed (suite completa)

## Notes / deviations
- Ninguna desviación del spec aprobado. `HTTPError` se trata como respuesta
  (devuelve status + body) para que `complete()` centralice el error con
  detalle; `URLError` (red caída) se envuelve en `LLMError` con la causa.
