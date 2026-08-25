# Requirements — agent_graph

> Feature 4 of `settings_files_tasks.json`. Status: `spec_ready` (awaiting human approval).

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

## R10 (anti prompt-injection)
The system MUST sanitize the transcript in a dedicated module
(`src/agent/sanitize.py`) BEFORE any LLM call: remove control characters,
zero-width and bidi-override characters, and cap the transcript length.

## R11 (anti prompt-injection)
IF the sanitized transcript exceeds `MAX_TRANSCRIPT_CHARS` THEN the guardrail
MUST end the run in state `failed` with `error_reason` explaining the length
limit, before any LLM call.

## R12 (anti prompt-injection)
WHEN a transcript line matches a known instruction-injection pattern (e.g.
"ignore previous instructions", "system prompt", "you are now", fake
`<system>`/`<assistant>` role tags) THEN the guardrail MUST remove those lines
from the text sent to the LLM and record each removal in
`state.sanitization_flags`; the flags MUST NOT alter the scoring verdict
silently — they are surfaced with the run.

## R13 (anti prompt-injection, defense in depth)
The scoring prompt (feature 5, `build_prompt`) MUST frame the transcript as
untrusted data inside explicit delimiters, with instructions to treat its
content as a transcript to score and never as instructions to follow.
