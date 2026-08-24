# Implementation — frontend_dashboard

## Traceability
- R1 → `test_create_run_sends_transcript_and_call_type` (radio kick-off/coaching + text_area en la vista; el cliente envía transcript y call_type)
- R2 → `test_run_url_and_status_shown`; polling `_poll_until_done` (~2 s) en `src/frontend/app.py`
- R3 → `test_get_run_completed_returns_report` + `_render_report` (one thing, brief, red flags, grade+banda, 12 dimensiones con evidencia y quick fix)
- R4 → `test_failed_reason_surfaced` (+ `st.error` destacado en la vista)
- R5 → `test_pdf_download_url_and_bytes`, `test_api_error_reason_propagated_409_pdf_not_ready`
- R6 → pestaña "Open an existing run" por id/URL; `test_get_run_completed_returns_report`
- R7 → `test_api_error_reason_propagated_422`, `test_unknown_run_maps_to_clear_error`, `test_transport_failure_is_mapped`, `test_non_json_error_body_still_yields_a_reason`, `test_empty_transcript_is_rejected_with_a_reason`

## Tasks checklist (specs/frontend_dashboard/tasks.md)
- [x] T0 — Decisión registrada en `docs/ADR.md`: Streamlit + httpx.
- [x] T1–T4 — `src/frontend/api_client.py`: `ScoringApiClient` (`create_run`, `get_run`, `download_pdf`) y `ApiClientError(reason, status_code)`.
- [x] T5 — `src/frontend/app.py`: 2 opciones de evaluación, text_area, URL del run, polling, reporte, fallo destacado, botón PDF.
- [x] T6 — `tests/test_frontend_client.py` con `httpx.MockTransport` (11 tests).
- [x] T7 — `uv run pytest`: 125 passed. Smoke test: app arranca headless (HTTP 200).

## Notes / decisions during implementation
- `create_run` valida localmente con `CreateRunRequest` (mismo modelo que la API):
  un transcript vacío falla en el cliente con `ApiClientError` antes de tocar
  la red; misma contract que un 422 del servidor.
- `_reason_from` prefiere el `detail` estructurado de FastAPI (incluido el
  formato lista de 422) y cae al cuerpo crudo si no es JSON: nunca hay fallo
  silencioso ni genérico.
- Los bytes del PDF se cachean por run en `st.session_state["pdf_cache"]` para
  no refetchear en cada rerender de Streamlit.
- El botón "Evaluate" usa `st.rerun()` tras el polling para renderizar el
  resultado final desde el estado persistido (misma ruta que R6).
