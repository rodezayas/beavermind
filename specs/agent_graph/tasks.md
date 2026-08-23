# Tasks — agent_graph

- [ ] T1 — Add `langgraph` dependency (approved set). Covers: R1.
- [ ] T2 — Create `src/agent/state.py` with `ScoringState`. Covers: R2.
- [ ] T3 — Create `src/agent/nodes.py` with `router_node` and conditional routing values. Covers: R3, R4, R7.
- [ ] T4 — Implement `guardrail_node` (empty / <4 turns → failed). Covers: R5, R7.
- [ ] T5 — Implement `score_kickoff_node` and `score_coaching_node` delegating to `scoring_report`. Covers: R7, R8.
- [ ] T6 — Implement error boundary: node exceptions → failed state with reason. Covers: R6.
- [ ] T7 — Create `src/agent/graph.py` with `build_graph()` and `run_scoring()`. Covers: R1, R9.
- [ ] T8 — Write `test_router_routes_to_kickoff_branch` / `test_router_routes_to_coaching_branch`. Covers: R3.
- [ ] T9 — Write `test_router_fails_on_missing_call_type`. Covers: R4.
- [ ] T10 — Write `test_guardrail_rejects_empty_transcript` and `test_guardrail_rejects_short_transcript`. Covers: R5.
- [ ] T11 — Write `test_scorer_exception_marks_run_failed`. Covers: R6.
- [ ] T12 — Write `test_completed_scoring_sets_report_and_status`. Covers: R8.
- [ ] T13 — Run `uv run pytest`; suite green. Covers: R1–R9.
