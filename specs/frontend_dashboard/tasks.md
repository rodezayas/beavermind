# Tasks — frontend_dashboard

- [ ] T0 — HUMAN: decide the technology (Streamlit vs React+Node) and record it in `docs/ADR.md`. Covers: design.md.
- [ ] T1 — Create `src/frontend/api_client.py` with `ScoringApiClient` and `ApiClientError`. Covers: R2, R7, R8.
- [ ] T2 — Implement `create_run(transcript, call_type)` mapping 201/422. Covers: R1, R2.
- [ ] T3 — Implement `get_run(run_id)` returning view state (status, report | error_reason). Covers: R3, R4, R6.
- [ ] T4 — Implement `download_pdf(run_id)` returning bytes. Covers: R5.
- [ ] T5 — Create the view (per T0 decision): form, live status polling, report render, PDF button. Covers: R1–R6.
- [ ] T6 — Write `tests/test_frontend_client.py`: create/get/pdf/error paths with a fake HTTP layer. Covers: R2–R7, R8.
- [ ] T7 — Run `uv run pytest`; suite green. Covers: R1–R8.
