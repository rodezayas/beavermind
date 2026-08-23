# Tasks — agent_graph

- [x] T1 — Add `langgraph` dependency (approved set). Covers: R1.
- [x] T2 — Create `src/agent/state.py` with `ScoringState` (incl. `sanitization_flags`). Covers: R2.
- [x] T3 — Create `src/agent/sanitize.py` with `sanitize_transcript()` (control/zero-width/bidi chars, length cap, injection patterns). Covers: R10, R11, R12.
- [x] T4 — Create `src/agent/nodes.py` with `router_node` and routing helpers. Covers: R3, R4, R7.
- [x] T5 — Implement `guardrail_node` (empty / <4 turns / oversized → failed; sanitiza y flagea). Covers: R5, R7, R10–R12.
- [x] T6 — Implement `make_score_node(call_type, scoring_fn)` con error boundary. Covers: R6, R7, R8.
- [x] T7 — Create `src/agent/graph.py` with `build_graph(scoring_fn)` and `run_scoring(run, scoring_fn)`. Covers: R1, R9.
- [x] T8 — Write `test_router_routes_to_kickoff_branch` / `test_router_routes_to_coaching_branch`. Covers: R3.
- [x] T9 — Write `test_router_fails_on_missing_call_type`. Covers: R4.
- [x] T10 — Write `test_guardrail_rejects_empty_transcript` and `test_guardrail_rejects_short_transcript`. Covers: R5.
- [x] T11 — Write `test_scorer_exception_marks_run_failed`. Covers: R6.
- [x] T12 — Write `test_completed_scoring_sets_report_and_status`. Covers: R8.
- [x] T13 — Write `test_sanitize_strips_control_and_zero_width_chars`. Covers: R10.
- [x] T14 — Write `test_guardrail_rejects_oversized_transcript`. Covers: R11.
- [x] T15 — Write `test_injection_lines_removed_and_flagged`. Covers: R12.
- [x] T16 — Run `uv run pytest`; suite green. Covers: R1–R13.
