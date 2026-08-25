# Implementation — frontend_dashboard

## Traceability
- R1 → `test_create_run_sends_transcript_and_call_type` (kick-off/coaching radio + text_area in the view; the client sends transcript and call_type)
- R2 → `test_run_url_and_status_shown`; polling `_poll_until_done` (~2 s) in `src/frontend/app.py`
- R3 → `test_get_run_completed_returns_report` + `_render_report` (one thing, brief, red flags, grade+band, 12 dimensions with evidence and quick fix)
- R4 → `test_failed_reason_surfaced` (+ highlighted `st.error` in the view)
- R5 → `test_pdf_download_url_and_bytes`, `test_api_error_reason_propagated_409_pdf_not_ready`
- R6 → "Open an existing run" tab by id/URL; `test_get_run_completed_returns_report`
- R7 → `test_api_error_reason_propagated_422`, `test_unknown_run_maps_to_clear_error`, `test_transport_failure_is_mapped`, `test_non_json_error_body_still_yields_a_reason`, `test_empty_transcript_is_rejected_with_a_reason`

## Tasks checklist (specs/frontend_dashboard/tasks.md)
- [x] T0 — Decision recorded in `docs/ADR.md`: Streamlit + httpx.
- [x] T1–T4 — `src/frontend/api_client.py`: `ScoringApiClient` (`create_run`, `get_run`, `download_pdf`) and `ApiClientError(reason, status_code)`.
- [x] T5 — `src/frontend/app.py`: 2 evaluation options, text_area, run URL, polling, report, highlighted failure, PDF button.
- [x] T6 — `tests/test_frontend_client.py` with `httpx.MockTransport` (11 tests).
- [x] T7 — `uv run pytest`: 125 passed. Smoke test: app starts headless (HTTP 200).

## Notes / decisions during implementation
- `create_run` validates locally with `CreateRunRequest` (same model as the API):
  an empty transcript fails on the client with `ApiClientError` before touching
  the network; same contract as a 422 from the server.
- `_reason_from` prefers FastAPI's structured `detail` (including the
  list format of 422) and falls back to the raw body if it is not JSON: there is never
  a silent or generic failure.
- The PDF bytes are cached per run in `st.session_state["pdf_cache"]` to
  avoid refetching on every Streamlit rerender.
- The "Evaluate" button uses `st.rerun()` after polling to render the
  final result from persisted state (same path as R6).
