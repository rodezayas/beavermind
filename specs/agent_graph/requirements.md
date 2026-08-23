# Requirements — agent_graph

> Feature 4 de `settings_files_tasks.json`. Estado: `spec_ready` (esperando aprobación humana).

## R1
The system MUST implement the scoring pipeline as a LangGraph graph composed
of nodes defined in `src/agent/nodes.py`, a typed state in `src/agent/state.py`
and the graph assembly in `src/agent/graph.py` (one concern per file).

## R2
The graph state MUST be a typed model (not a bare dict) carrying at least:
`run_id`, `call_type`, `transcript`, `status`, `report` (optional),
`error_reason` (optional) and a `current_node` marker recording progress.

## R3
WHEN the graph starts THEN a router node MUST select the scoring branch from
`call_type`: `kickoff` routes to the kickoff scorer, `coaching` routes to the
coaching scorer.

## R4
IF `call_type` is missing or has no scoring branch THEN the graph MUST end in
state `failed` with `error_reason` naming the invalid call type.

## R5
WHEN the transcript is empty or contains fewer than 4 speaker turns
(lines starting with `[`) THEN the guardrail node MUST end the run in state
`failed` with `error_reason` explaining that the transcript is too short to
score, before any LLM call is made.

## R6
IF an exception escapes a scoring node THEN the graph MUST transition to
state `failed`, store the exception message in `error_reason` and MUST NOT
propagate the exception out of the graph invocation.

## R7
Each node MUST be a pure function with signature `(state: ScoringState) ->
ScoringState` so nodes are individually testable.

## R8
WHEN a scoring node runs THEN the state MUST be updated with the resulting
`report` (via `scoring_report`, feature 5) and `status: completed` before the
graph ends.

## R9
The graph MUST expose a single entry point `build_graph()` returning the
compiled LangGraph runnable, and `run_scoring(run: Run, ...) -> ScoringState`
as the only invocation API used by the API layer.
