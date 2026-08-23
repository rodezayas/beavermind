"""Graph assembly and the single invocation API for the scoring pipeline.

`build_graph` wires the LangGraph topology; `run_scoring` is the only entry
point the API layer uses, mapping a persisted `Run` to the graph state and
back.
"""

from langgraph.graph import END, StateGraph

from src.agent.nodes import (
    ScoringFn,
    guardrail_node,
    make_score_node,
    route_after_guardrails,
    route_after_router,
    router_node,
)
from src.agent.state import ScoringState
from src.schemas import CallType, Run


def build_graph(scoring_fn: ScoringFn):
    """Compile the scoring graph for the given scoring function.

    Topology: router -> guardrails -> (score_kickoff | score_coaching) -> END,
    with conditional edges sending blocked runs straight to END carrying a
    failed state.

    Args:
        scoring_fn: Scoring function per rubric branch (feature 5 in prod,
            a fake in tests).

    Returns:
        The compiled LangGraph runnable.
    """
    graph = StateGraph(ScoringState)
    graph.add_node("router", router_node)
    graph.add_node("guardrails", guardrail_node)
    graph.add_node("score_kickoff", make_score_node(CallType.KICKOFF, scoring_fn))
    graph.add_node("score_coaching", make_score_node(CallType.COACHING, scoring_fn))

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router", route_after_router, {"guardrails": "guardrails", "__end__": END}
    )
    graph.add_conditional_edges(
        "guardrails",
        route_after_guardrails,
        {
            "score_kickoff": "score_kickoff",
            "score_coaching": "score_coaching",
            "__end__": END,
        },
    )
    for scorer in ("score_kickoff", "score_coaching"):
        graph.add_edge(scorer, END)
    return graph.compile()


def state_from_run(run: Run) -> ScoringState:
    """Build the initial graph state from a persisted run."""
    return ScoringState(
        run_id=run.run_id,
        call_type=run.call_type,
        transcript=run.transcript,
        status=run.status,
    )


def run_scoring(run: Run, scoring_fn: ScoringFn) -> ScoringState:
    """Score a run end-to-end; the only invocation API for the API layer.

    Args:
        run: Persisted run with transcript and call type.
        scoring_fn: Scoring function per rubric branch.

    Returns:
        The final graph state (completed with report, or failed with reason).
    """
    final_state = build_graph(scoring_fn).invoke(state_from_run(run))
    return ScoringState.model_validate(final_state)


__all__ = ["build_graph", "run_scoring", "state_from_run"]
