"""HTTP request/response models for the scoring API.

Kept separate from the domain models in `src/schemas.py`: the wire contract
can evolve without touching the domain (and vice versa).
"""

from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas import CallType, Report, RunStatus


class CreateRunRequest(BaseModel):
    """Body of POST /runs."""

    transcript: str = Field(min_length=1)  # empty transcripts are 422 (R3)
    call_type: CallType


class CreateRunResponse(BaseModel):
    """Response of POST /runs: the run id and its public URL (R2)."""

    run_id: UUID
    url: str
    status: RunStatus


class RunResponse(BaseModel):
    """Response of GET /runs/{run_id} (R4)."""

    run_id: UUID
    call_type: CallType
    status: RunStatus
    report: Report | None = None
    error_reason: str | None = None


class ErrorResponse(BaseModel):
    """Uniform error body; carries a human-readable reason, never secrets."""

    detail: str


__all__ = [
    "CreateRunRequest",
    "CreateRunResponse",
    "ErrorResponse",
    "RunResponse",
]
