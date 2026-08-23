"""Graph nodes for the scoring pipeline.

Every node is a pure function `ScoringState -> ScoringState` so nodes are
individually testable. Scorer nodes are built by a factory that closes over
the injected scoring function; the error boundary lives there so no exception
ever escapes a node (the graph always ends in a well-defined state).
"""

from collections.abc import Callable

from src.agent.sanitize import (
    MIN_SPEAKER_TURNS,
    count_speaker_turns,
    sanitize_transcript,
)
from src.agent.state import ScoringState
from src.schemas import CallType, Report, RunStatus

#: Signature of the scoring function injected into the graph (feature 5)
ScoringFn = Callable[[CallType, str], Report]


def _fail(state: ScoringState, reason: str, node: str) -> ScoringState:
    """Return the state marked failed with an explicit reason."""
    return state.copy_as_failed(reason=reason, node=node)


def router_node(state: ScoringState) -> ScoringState:
    """Validate the call type and mark progress; never scores anything.

    Fails the run when `call_type` is missing (R4); branch selection itself is
    a conditional edge decided by `route_after_router`.
    """
    state = state.model_copy(update={"current_node": "router"})
    if state.call_type is None:
        return _fail(state, "missing call_type: cannot select a rubric branch", "router")
    return state


def route_after_router(state: ScoringState) -> str:
    """Conditional edge: to guardrails, or end when the router failed."""
    if state.status is RunStatus.FAILED:
        return "__end__"
    return "guardrails"


def guardrail_node(state: ScoringState) -> ScoringState:
    """Sanitize the transcript and enforce the minimum-structure rules.

    Order matters: sanitize first (R10-R12), then length cap (R11), then the
    speaker-turn minimum (R5). All failures happen before any LLM call.
    """
    state = state.model_copy(update={"current_node": "guardrails"})
    if not state.transcript.strip():
        return _fail(state, "transcript is empty: nothing to score", "guardrails")

    result = sanitize_transcript(state.transcript)
    if result.too_long:
        return _fail(
            state,
            f"transcript exceeds the maximum of {len(result.text)} characters "
            "after sanitization",
            "guardrails",
        )
    if count_speaker_turns(result.text) < MIN_SPEAKER_TURNS:
        return _fail(
            state,
            f"transcript has fewer than {MIN_SPEAKER_TURNS} speaker turns: "
            "too short to score",
            "guardrails",
        )
    return state.model_copy(
        update={
            "transcript": result.text,
            "sanitization_flags": result.flags,
            "status": RunStatus.SCORING,
        }
    )


def route_after_guardrails(state: ScoringState) -> str:
    """Conditional edge: to the rubric branch scorer, or end when blocked."""
    if state.status is RunStatus.FAILED:
        return "__end__"
    assert state.call_type is not None  # router guarantees this
    return f"score_{state.call_type.value}"


def make_score_node(
    call_type: CallType, scoring_fn: ScoringFn
) -> Callable[[ScoringState], ScoringState]:
    """Build a pure scorer node for one rubric branch.

    The returned node calls the injected `scoring_fn`, stores the report and
    completes the run. Any exception is converted into a failed state (R6):
    errors are persisted as run failures, never propagated out of the graph.
    """
    node_name = f"score_{call_type.value}"

    def score_node(state: ScoringState) -> ScoringState:
        state = state.model_copy(update={"current_node": node_name})
        try:
            report = scoring_fn(call_type, state.transcript)
        except Exception as exc:  # noqa: BLE001 - boundary by design (R6)
            return _fail(state, f"scoring failed: {exc}", node_name)
        return state.model_copy(
            update={"report": report, "status": RunStatus.COMPLETED}
        )

    score_node.__name__ = node_name
    score_node.__doc__ = f"Score the transcript against the {call_type.value} rubric."
    return score_node


__all__ = [
    "ScoringFn",
    "guardrail_node",
    "make_score_node",
    "route_after_guardrails",
    "route_after_router",
    "router_node",
]
