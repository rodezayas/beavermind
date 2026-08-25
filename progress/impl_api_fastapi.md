# Implementation — api_fastapi

## Traceability
- R1 → `test_app_factory_with_fakes` (factory + DI without globals)
- R2 → `test_post_run_creates_and_scores` (201, URL, scoring in background)
- R3 → `test_post_run_invalid_body` (empty transcript and unknown call_type → 422)
- R4 → `test_get_run_completed_returns_report`, `test_get_run_failed_returns_reason`
- R5 → `test_get_run_not_found`
- R6 → `test_pdf_endpoint_returns_attachment` (application/pdf + attachment + %PDF)
- R7 → `test_pdf_endpoint_conflicts_when_not_completed` (409 with reason)
- R8 → `test_background_outcome_persisted` (the result lives in the repository after closing the "tab")
- R9 → `test_error_messages_contain_no_secrets`

## Tasks checklist (specs/api_fastapi/tasks.md)
- [x] T1–T12 completed; `uv run pytest`: 111 passed.

## Notes / decisions during implementation
- The scoring pipeline is tested end to end with the REAL `build_report`
  over a fake LLM transport: the only simulated part is the network.
- `_score_in_background` persists every transition (pending → scoring →
  completed/failed); an exception from the pipeline also ends up failed
  with cause (it never leaves the run hanging in scoring).
- Fix during implementation: missing import of `run_scoring` detected by
  `test_background_outcome_persisted` (the boundary turned it into a run
  failed with cause — the safety net worked).
