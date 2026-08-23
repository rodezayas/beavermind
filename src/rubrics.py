"""Loading and parsing of the scoring rubrics.

The rubrics live as markdown files under `rubrics/` and are the single source
of truth. This module parses them into typed objects: 12 dimensions with max
points, the canonical score bands, the global automatic score caps, and the
optional-dimension flag used by the coaching rubric.
"""

import re
from pathlib import Path

from pydantic import BaseModel, ValidationError, model_validator

from src.schemas import CallType

#: Directory that holds the rubric markdown files by default
DEFAULT_RUBRICS_DIR = Path("rubrics")

#: Markdown file per call type (names match the files shipped in `rubrics/`)
_RUBRIC_FILES: dict[CallType, str] = {
    CallType.COACHING: "coaching-call-rubric.md",
    CallType.KICKOFF: "kickotff-call-rubric.md",
}

#: Canonical total-score band names, in ascending order (pdf_format.md)
CANONICAL_BANDS: list[str] = ["Fail", "At risk", "Inconsistent", "Strong", "Elite"]

#: Normalization from the markdown band labels to canonical names
_BAND_ALIASES = {
    "ELITE": "Elite",
    "STRONG": "Strong",
    "INCONSISTENT": "Inconsistent",
    "AT RISK": "At risk",
    "FAIL": "Fail",
}

# Header like: `### Dimension 4 — Movement Coaching Quality (15 pts) — Optional`
_DIMENSION_HEADER = re.compile(
    r"^###\s+Dimension\s+(?P<id>\d+)\s+[—-]\s+(?P<name>.+?)\s+"
    r"\((?P<points>\d+)\s*pts\)(?P<optional>.*)$"
)

# Band reference row like: `| **ELITE** | 90–100 | Client feels seen... |`
_BAND_ROW = re.compile(r"^\|\s*\*\*(?P<label>[A-Z ]+)\*\*\s*\|")

# Cap table rows live between the "Global Automatic Score Caps" header and the
# next markdown header; the cap cell is parsed with the patterns below.
_CAPS_HEADER = re.compile(r"^#{2,3}\s+Global Automatic Score Caps")
_ANY_HEADER = re.compile(r"^#{1,6}\s")
_DIM_CAP = re.compile(
    r"(?P<max>\d+(?:\.\d+)?)\s*/\s*(?P<dim_max>\d+)\s+on\s+(?:D(?P<dim>\d+)|Dimension\s+(?P<dim_long>\d+))",
    re.I,
)
_TOTAL_CAP = re.compile(r"Max\s+(?P<total>\d+)\s+total", re.I)


class RubricParseError(ValueError):
    """Raised when a rubric markdown file cannot be parsed into a Rubric."""


class Dimension(BaseModel):
    """One scoring dimension of a rubric."""

    dimension_id: int
    name: str
    max_points: int
    optional: bool = False  # True for coaching D4 (Movement Coaching Quality)


class ScoreCap(BaseModel):
    """A global automatic score cap declared by the rubric."""

    condition: str  # rubric wording of when the cap fires
    dimension_id: int | None = None  # set when the cap targets one dimension
    max_dimension_score: int | None = None  # e.g. 10 in "Max 10/15 on D3"
    max_total: int | None = None  # e.g. 75 in "Max 75 total"


class Rubric(BaseModel):
    """Parsed rubric for one call type."""

    call_type: CallType
    dimensions: list[Dimension]
    bands: list[str]  # canonical names, e.g. ["Elite", "Strong", ...]
    score_caps: list[ScoreCap]

    @model_validator(mode="after")
    def _validate_structure(self) -> "Rubric":
        """Enforce the rubric invariants: 12 dimensions summing 100 points."""
        if len(self.dimensions) != 12:
            raise RubricParseError(
                f"{self.call_type} rubric must define 12 dimensions, "
                f"found {len(self.dimensions)}"
            )
        total = sum(d.max_points for d in self.dimensions)
        if total != 100:
            raise RubricParseError(
                f"{self.call_type} rubric dimensions must sum 100 points, "
                f"got {total}"
            )
        if set(self.bands) != set(CANONICAL_BANDS):
            raise RubricParseError(
                f"{self.call_type} rubric bands must be {CANONICAL_BANDS}, "
                f"got {self.bands}"
            )
        return self

    def max_possible(self, disabled_ids: frozenset[int] | set[int] = frozenset()) -> int:
        """Total points available when the given dimension ids are disabled.

        The coaching rubric drops from 100 to 85 when its optional D4 is off.
        """
        return sum(
            d.max_points for d in self.dimensions if d.dimension_id not in disabled_ids
        )

    def optional_dimension_ids(self) -> list[int]:
        """Ids of the dimensions marked optional in the markdown."""
        return [d.dimension_id for d in self.dimensions if d.optional]


def _parse_dimensions(text: str, source: Path) -> list[Dimension]:
    """Extract the 12 `### Dimension N` sections from the markdown."""
    dimensions: list[Dimension] = []
    for line in text.splitlines():
        match = _DIMENSION_HEADER.match(line.strip())
        if not match:
            continue
        optional = "optional" in match.group("optional").lower()
        dimensions.append(
            Dimension(
                dimension_id=int(match.group("id")),
                name=match.group("name").strip(),
                max_points=int(match.group("points")),
                optional=optional,
            )
        )
    if not dimensions:
        raise RubricParseError(f"No dimension headers found in {source}")
    return dimensions


def _parse_bands(text: str, source: Path) -> list[str]:
    """Extract canonical band names from the 'Scoring Bands Reference' table."""
    bands: list[str] = []
    for line in text.splitlines():
        match = _BAND_ROW.match(line.strip())
        if not match:
            continue
        label = match.group("label").strip()
        canonical = _BAND_ALIASES.get(label)
        if canonical is not None:
            bands.append(canonical)
    if not bands:
        raise RubricParseError(f"No scoring bands reference found in {source}")
    return bands


def _parse_caps(text: str, source: Path) -> list[ScoreCap]:
    """Extract the 'Global Automatic Score Caps' table rows."""
    caps: list[ScoreCap] = []
    in_caps_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if _CAPS_HEADER.match(stripped):
            in_caps_section = True
            continue
        if in_caps_section and _ANY_HEADER.match(stripped):
            break  # caps section ended
        if not in_caps_section or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("Condition", ":---", "---"):
            continue  # table header / separator
        condition, cap_cell = cells[0], cells[1]
        dim_match = _DIM_CAP.search(cap_cell)
        total_match = _TOTAL_CAP.search(cap_cell)
        if dim_match:
            dim_id = dim_match.group("dim") or dim_match.group("dim_long")
            caps.append(
                ScoreCap(
                    condition=condition,
                    dimension_id=int(dim_id),
                    max_dimension_score=int(float(dim_match.group("max"))),
                )
            )
        elif total_match:
            caps.append(
                ScoreCap(
                    condition=condition,
                    max_total=int(total_match.group("total")),
                )
            )
        else:
            raise RubricParseError(
                f"Unparseable score cap in {source}: {cap_cell!r}"
            )
    return caps


def load_rubric(
    call_type: CallType, rubrics_dir: Path | str = DEFAULT_RUBRICS_DIR
) -> Rubric:
    """Load and parse the rubric markdown for the given call type.

    Args:
        call_type: Which rubric to load (kickoff or coaching).
        rubrics_dir: Directory holding the markdown files (injectable for tests).

    Returns:
        A validated `Rubric`.

    Raises:
        RubricParseError: If the file is missing or cannot be parsed.
    """
    filename = _RUBRIC_FILES.get(call_type)
    if filename is None:
        raise RubricParseError(f"No rubric mapping for call type {call_type!r}")
    path = Path(rubrics_dir) / filename
    if not path.is_file():
        raise RubricParseError(
            f"Rubric file for call type {call_type.value!r} not found at {path}"
        )
    text = path.read_text(encoding="utf-8")
    try:
        return Rubric(
            call_type=call_type,
            dimensions=_parse_dimensions(text, path),
            bands=_parse_bands(text, path),
            score_caps=_parse_caps(text, path),
        )
    except ValidationError as exc:
        # Re-wrap pydantic's error so callers only handle RubricParseError.
        raise RubricParseError(f"Invalid rubric structure in {path}: {exc}") from exc


__all__ = [
    "CANONICAL_BANDS",
    "Dimension",
    "Rubric",
    "RubricParseError",
    "ScoreCap",
    "load_rubric",
]
