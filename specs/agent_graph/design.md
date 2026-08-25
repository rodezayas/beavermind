# Design — agent_graph

> How feature 4 is built. Decisions made before writing any code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/agent/__init__.py` | create | package |
| `src/agent/state.py` | create | `ScoringState` (typed state model) |
| `src/agent/sanitize.py` | create | `sanitize_transcript()` — anti prompt-injection |
| `src/agent/nodes.py` | create | `router_node`, `guardrail_node`, scorer factories, routing helpers |
| `src/agent/graph.py` | create | `build_graph()`, `run_scoring()` |
| `tests/test_agent_graph.py` | create | covers R2–R12 |
| `pyproject.toml` | modify | add `langgraph` (approved) |

## New signatures

```python
# src/agent/state.py
class ScoringState(BaseModel):
    run_id: UUID
    call_type: CallType | None
    transcript: str          # already sanitized once past guardrails
    status: RunStatus
    report: Report | None = None
    error_reason: str | None = None
    current_node: str = "start"   # progress, survives the tab closing
    sanitization_flags: list[str] = []  # R12: removed injection lines

# src/agent/sanitize.py
MAX_TRANSCRIPT_CHARS = 60_000
class SanitizationResult(BaseModel):
    text: str; flags: list[str]; too_long: bool
def sanitize_transcript(text: str) -> SanitizationResult

# src/agent/nodes.py  (all pure: state in -> state out, R7)
def router_node(state: ScoringState) -> ScoringState
def guardrail_node(state: ScoringState) -> ScoringState   # R5, R10–R12
def make_score_node(call_type: CallType, scoring_fn: ScoringFn) -> NodeFn
def route_after_router(state) -> str   # "guardrails" | END
def route_after_guardrails(state) -> str  # scorer name | END

# src/agent/graph.py
ScoringFn = Callable[[CallType, str], Report]  # injectable; feature 5 provides it
def build_graph(scoring_fn: ScoringFn) -> CompiledGraph   # R9
def run_scoring(run: Run, scoring_fn: ScoringFn) -> ScoringState
```

## Graph topology

```
START -> router -> guardrails -> (score_kickoff | score_coaching) -> END
                     |                        |
                     +-------> END <----------+  (failed status kept in the state)
```

- Conditional edge 1 (router): to `guardrails` or `END` depending on the
  validity of `call_type` (R3, R4).
- Conditional edge 2 (guardrails): to the corresponding scorer or `END`
  with a failed status (R5, R11).
- The error boundary lives inside `make_score_node` (try/except → failed,
  R6): LangGraph never sees an exception leave a node.

## Decisions
- **`scoring_fn` injected into `build_graph`** (typed as `ScoringFn`): the graph
  does not depend on the scoring implementation (feature 5); tests inject a
  fake and the API (feature 7) wires up `src.scoring`. Same DI pattern as
  `GroqClient`.
- **LangGraph StateGraph with a Pydantic model as state_schema**: the typed
  state (R2) travels between nodes and is serializable to persist progress.
- **Guardrail before the scorer** (R5): avoids spending LLM tokens on useless
  transcripts; the minimum of 4 `[Speaker]:` turns prevents false positives.
- **Deterministic sanitization, not LLM-based** (R10–R12): regex + character
  cleanup; a sanitizer based on another LLM would be circular and not auditable.
- **`current_node` + `sanitization_flags` in the state**: minimal progress and
  audit data, persistable by the database layer.

## Alternative discarded
- A single monolithic node with `if call_type == ...`: discarded because it mixes
  router, guardrails and scoring in one function that cannot be tested separately
  (violates R7 and the "one concern per file" rule from AGENTS.md).

## Traceability preview
- R3 → `test_router_routes_to_kickoff_branch` / `..._coaching_branch`
- R4 → `test_router_fails_on_missing_call_type`
- R5 → `test_guardrail_rejects_empty_transcript`, `test_guardrail_rejects_short_transcript`
- R6 → `test_scorer_exception_marks_run_failed`
- R7 → tests invoke nodes individually
- R8 → `test_completed_scoring_sets_report_and_status`
- R10 → `test_sanitize_strips_control_and_zero_width_chars`
- R11 → `test_guardrail_rejects_oversized_transcript`
- R12 → `test_injection_lines_removed_and_flagged`
- R13 → verified in the `scoring_report` spec (R8); cross-checked when implementing it
