"""Core domain models shared by every layer of the scoring system.

These Pydantic models are the contract between the API, the LangGraph agent,
the database layer and the PDF renderer. Validation rules live here so callers
cannot persist an invalid run or an invalid report.
"""

from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


def _utcnow() -> datetime:
    """Return the current UTC time (used as default timestamp)."""
    return datetime.now(timezone.utc)


class CallType(StrEnum):
    """Kind of call being scored; selects which rubric applies."""

    KICKOFF = "kickoff"
    COACHING = "coaching"


class RunStatus(StrEnum):
    """Lifecycle of a scoring run."""

    PENDING = "pending"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


class OneThing(BaseModel):
    """The single change that would move the score the most."""

    change: str  # what the coach should do differently
    projected_score: float  # score the call would reach with the change applied


class Grade(BaseModel):
    """Total score and the band it lands in."""

    total: float
    band: str  # one of the rubric's canonical band names
    max_possible: float = 100.0  # 85 when coaching D4 is disabled


class DimensionScore(BaseModel):
    """Score, reasoning and evidence for one rubric dimension."""

    dimension_id: int
    name: str
    max_points: int
    score: float | None = None  # None only when the dimension is disabled
    band: str | None = None  # per-dimension band label (e.g. "Elite")
    reasoning: str
    transcript_lines: list[str] = Field(default_factory=list)  # quoted evidence
    quick_fix: str  # what the coach had to do to reach full marks
    disabled: bool = False
    disabled_reason: str | None = None

    @model_validator(mode="after")
    def _validate_disabled(self) -> "DimensionScore":
        """Enforce the optional-dimension contract (spec R8)."""
        if self.disabled:
            if self.score is not None or self.band is not None:
                raise ValueError(
                    f"D{self.dimension_id} is disabled: score and band must be None"
                )
            if not self.disabled_reason:
                raise ValueError(
                    f"D{self.dimension_id} is disabled: disabled_reason is required"
                )
        return self


class Report(BaseModel):
    """Full scoring report rendered to the coach (and to the PDF)."""

    one_thing: OneThing
    brief: str  # a few sentences on how the call went, written to the coach
    red_flags: list[str] = Field(default_factory=list)  # churn-risk signals
    grade: Grade
    dimensions: list[DimensionScore]

    @model_validator(mode="after")
    def _validate_twelve_dimensions(self) -> "Report":
        """A report must cover exactly the 12 rubric dimensions (spec R9)."""
        if len(self.dimensions) != 12:
            raise ValueError(
                f"Report must contain exactly 12 dimensions, got {len(self.dimensions)}"
            )
        return self


class Run(BaseModel):
    """A scoring run: its input, lifecycle state and outcome."""

    run_id: UUID = Field(default_factory=uuid4)  # also the public URL id
    call_type: CallType
    transcript: str
    status: RunStatus = RunStatus.PENDING
    report: Report | None = None  # set when completed
    error_reason: str | None = None  # mandatory when failed
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="after")
    def _validate_failed(self) -> "Run":
        """A failed run must say why (spec R6)."""
        if self.status is RunStatus.FAILED and not self.error_reason:
            raise ValueError("A failed run requires a non-empty error_reason")
        return self
