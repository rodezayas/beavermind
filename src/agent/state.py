"""Typed state carried through the scoring graph.

The state is a Pydantic model (never a bare dict) so every node has a typed
contract and the whole state can be serialized to persist run progress.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas import CallType, Report, RunStatus


class ScoringState(BaseModel):
    """State of one scoring run as it travels through the graph nodes.

    Attributes:
        run_id: Public id of the run (matches the persisted Run).
        call_type: Selected rubric branch; None until validated.
        transcript: Call transcript; already sanitized after guardrails.
        status: Lifecycle status mirrored from the Run.
        report: Completed scoring report, set by a scorer node.
        error_reason: Why the run failed; mandatory when status is failed.
        current_node: Progress marker (survives tab close via persistence).
        sanitization_flags: Audit log of removed injection attempts.
    """

    run_id: UUID
    call_type: CallType | None = None
    transcript: str
    status: RunStatus = RunStatus.PENDING
    report: Report | None = None
    error_reason: str | None = None
    current_node: str = "start"
    sanitization_flags: list[str] = Field(default_factory=list)

    def copy_as_failed(self, reason: str, node: str) -> "ScoringState":
        """Return a copy marked failed with the given reason (explicit path)."""
        return self.model_copy(
            update={
                "status": RunStatus.FAILED,
                "error_reason": reason,
                "current_node": node,
            }
        )


__all__ = ["ScoringState"]
