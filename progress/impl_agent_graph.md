# Implementation — agent_graph

## Traceability
- R1 → structure `src/agent/{state,sanitize,nodes,graph}.py` + `langgraph` in pyproject
- R2 → `test_state_is_typed_and_serializable`
- R3 → `test_router_routes_to_kickoff_branch`, `test_router_routes_to_coaching_branch`
- R4 → `test_router_fails_on_missing_call_type`
- R5 → `test_guardrail_rejects_empty_transcript`, `test_guardrail_rejects_short_transcript`
- R6 → `test_scorer_exception_marks_run_failed`
- R7 → all nodes are pure functions; tests invoke them individually
- R8 → `test_completed_scoring_sets_report_and_status`, `test_run_scoring_maps_run_to_state_and_back`
- R10 → `test_sanitize_strips_control_and_zero_width_chars`, `test_sanitize_keeps_clean_transcript_untouched`
- R11 → `test_guardrail_rejects_oversized_transcript`
- R12 → `test_injection_lines_removed_and_flagged` (5 payloads), `test_injection_removed_before_scoring_fn_sees_it`, `test_sanitize_preserves_legitimate_content`
- R13 → belongs to `scoring_report` (R8 of its spec); cross-check pending that feature

## Tasks checklist (specs/agent_graph/tasks.md)
- [x] T1–T16 completed (see spec file); `uv run pytest`: 48 passed.

## Notes / decisions during implementation
- **`scoring_fn` injected into `build_graph`/`run_scoring`** (adjustment of the design
  approved in the updated spec): the graph is not coupled to feature 5; the API
  (feature 7) will wire up `src.scoring` and tests use fakes. Specified this way
  in `specs/agent_graph/design.md` before coding.
- **Two-layer sanitization** (refined during T3): verbal injection
  patterns only apply at the start of a line/turn (avoids false positives with
  quoted speech, covered by `test_sanitize_preserves_legitimate_content`);
  fake role tags `<system>/<assistant>` are removed in any
  position. Polite prefixes ("please reveal...") are also covered.
- The error boundary turns any scorer exception into failed state
  (R6): the exception never crosses the graph boundary.
