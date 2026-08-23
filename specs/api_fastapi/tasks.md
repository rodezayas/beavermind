# Tasks — api_fastapi

- [ ] T1 — Create `src/api/schemas.py` with HTTP request/response models. Covers: R2, R3, R4.
- [ ] T2 — Create `src/api/dependencies.py` with DI providers. Covers: R1.
- [ ] T3 — Create `src/api/routes.py` with `POST /runs` (validation, persist pending, background scoring). Covers: R2, R3, R8.
- [ ] T4 — Add `GET /runs/{run_id}` (status/report/error). Covers: R4, R5.
- [ ] T5 — Add `GET /runs/{run_id}/report.pdf` (attachment / 409). Covers: R6, R7.
- [ ] T6 — Create `src/api/app.py` with `create_app(repo, llm)`. Covers: R1.
- [ ] T7 — Write `test_post_run_creates_and_scores` and `test_post_run_invalid_body`. Covers: R2, R3.
- [ ] T8 — Write `test_get_run_completed_returns_report`, `test_get_run_failed_returns_reason`, `test_get_run_not_found`. Covers: R4, R5.
- [ ] T9 — Write `test_pdf_endpoint_returns_attachment` and `test_pdf_endpoint_conflicts_when_not_completed`. Covers: R6, R7.
- [ ] T10 — Write `test_background_outcome_persisted`. Covers: R8.
- [ ] T11 — Write `test_error_messages_contain_no_secrets`. Covers: R9.
- [ ] T12 — Run `uv run pytest`; suite green. Covers: R1–R9.
