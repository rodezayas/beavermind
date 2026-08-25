# Design — frontend_dashboard

> How feature 10 is built. **The technology is open**: this design
> records both options and the decision criterion. It is closed before
> implementing (human decision).

## Option A — Streamlit (workflow-beavermind.jpg)

| Aspect | Evaluation |
|---|---|
| Effort | Minimal: one page, `st.text_area`, `st.selectbox`, polling with `st.rerun` |
| Risk | Low: all Python, reuses `src/` directly |
| Cons | Less fine visual control; less elegant polling |

## Option B — React + Node.js

| Aspect | Evaluation |
|---|---|
| Effort | High: JS sub-project (build, tooling, CORS), duplicates types |
| Risk | Medium: new toolchain outside the Python repo |
| Cons | AGENTS.md is Python-first; every report type gets duplicated in TS |

## Decision criterion (for the human)
- If the dashboard is internal for the operator → **A (Streamlit)**: meets R1–R7
  with a fraction of the effort and zero new dependencies outside the stack.
- If the dashboard is a client-facing product with its own visual identity
  → **B (React)**: the extra cost buys full control of the look.

## Common structure (independent of the choice)

| File | Purpose |
|---|---|
| `src/frontend/api_client.py` | `ScoringApiClient`: `create_run()`, `get_run()`, `download_pdf()`; maps HTTP errors to `ApiClientError(reason)` |
| `src/frontend/app.<ext>` | the view: form, run status, report, PDF button |
| `tests/test_frontend_client.py` | R2–R7 coverage against a `FakeApi` (httpx MockTransport or own stub) |

## Decisions
- **The API client lives in testable Python** (`src/frontend/api_client.py`,
  R8) no matter what happens with the view: the call and error-handling logic
  is what's testable; rendering belongs to the framework.
- **Status polling** while `pending`/`scoring` (R2): fixed interval of
  ~2 s until `completed`/`failed`.
- **The technology decision is recorded in `docs/ADR.md`** before
  implementing (additional gate within this feature).

## Alternative discarded
- Serving the dashboard from FastAPI with Jinja2 + HTMX: discarded for now —
  it mixes API responsibilities (feature 7 already closed as a JSON API) with
  the view; will be reconsidered if the human chooses a middle ground.

## Traceability preview
- R1 → `test_create_run_sends_transcript_and_call_type`
- R2 → `test_run_url_and_status_shown`
- R3 → `test_completed_report_mapped_to_view`
- R4 → `test_failed_reason_surfaced`
- R5 → `test_pdf_download_url`
- R6 → `test_get_run_without_rescoring`
- R7 → `test_api_error_reason_propagated`
