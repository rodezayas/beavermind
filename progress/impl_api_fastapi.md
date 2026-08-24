# Implementation — api_fastapi

## Traceability
- R1 → `test_app_factory_with_fakes` (factory + DI sin globals)
- R2 → `test_post_run_creates_and_scores` (201, URL, scoring en background)
- R3 → `test_post_run_invalid_body` (transcript vacío y call_type desconocido → 422)
- R4 → `test_get_run_completed_returns_report`, `test_get_run_failed_returns_reason`
- R5 → `test_get_run_not_found`
- R6 → `test_pdf_endpoint_returns_attachment` (application/pdf + attachment + %PDF)
- R7 → `test_pdf_endpoint_conflicts_when_not_completed` (409 con razón)
- R8 → `test_background_outcome_persisted` (el resultado vive en el repository tras cerrar el "tab")
- R9 → `test_error_messages_contain_no_secrets`

## Tasks checklist (specs/api_fastapi/tasks.md)
- [x] T1–T12 completados; `uv run pytest`: 111 passed.

## Notes / decisions during implementation
- El pipeline de scoring se prueba de extremo a extremo con el `build_report`
  REAL sobre un transporte LLM falso: la única parte simulada es la red.
- `_score_in_background` persiste cada transición (pending → scoring →
  completed/failed); una excepción del pipeline también termina en failed
  con causa (nunca deja el run colgado en scoring).
- Fix durante implementación: import faltante de `run_scoring` detectado por
  `test_background_outcome_persisted` (el boundary lo convirtió en run
  failed con causa — la red de seguridad funcionó).
