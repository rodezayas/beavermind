"""Tests for src/rubrics.py (feature: rubric_loader)."""

from pathlib import Path

import pytest

from src.rubrics import CANONICAL_BANDS, RubricParseError, load_rubric
from src.schemas import CallType

FIXTURES = Path("tests/fixtures/rubrics")


def test_load_rubric_twelve_dimensions_sum_100():
    """R1, R2, R3: both real rubrics parse with 12 dimensions summing 100."""
    for call_type in (CallType.KICKOFF, CallType.COACHING):
        rubric = load_rubric(call_type)
        assert len(rubric.dimensions) == 12
        assert rubric.max_possible() == 100
        assert [d.dimension_id for d in rubric.dimensions] == list(range(1, 13))
        assert all(d.name for d in rubric.dimensions)


def test_band_names_exact():
    """R4: bands are exposed with the canonical names, nothing else."""
    rubric = load_rubric(CallType.COACHING)
    assert set(rubric.bands) == set(CANONICAL_BANDS)
    for expected in ("Elite", "Strong", "Inconsistent", "At risk", "Fail"):
        assert expected in rubric.bands


def test_score_caps_exposed():
    """R5: global automatic score caps are parsed from the markdown."""
    coaching = load_rubric(CallType.COACHING)
    dim_caps = {c.dimension_id: c for c in coaching.score_caps if c.dimension_id}
    total_caps = [c for c in coaching.score_caps if c.max_total is not None]
    assert dim_caps[3].max_dimension_score == 10
    assert dim_caps[10].max_dimension_score == 0
    assert any(c.max_total == 75 for c in total_caps)

    kickoff = load_rubric(CallType.KICKOFF)
    kickoff_dim_caps = {
        c.dimension_id: c for c in kickoff.score_caps if c.dimension_id
    }
    assert kickoff_dim_caps[4].max_dimension_score == 10
    assert any(c.max_total == 70 for c in kickoff.score_caps)


def test_coaching_d6_adjusted_cap_exposed():
    """R5: the D6 cap reflects the adjusted 10-point dimension (see README)."""
    coaching = load_rubric(CallType.COACHING)
    d6_cap = next(c for c in coaching.score_caps if c.dimension_id == 6)
    assert d6_cap.max_dimension_score == 7


def test_coaching_optional_d4_max_possible():
    """R6: coaching D4 is optional; disabling it drops the max to 85."""
    coaching = load_rubric(CallType.COACHING)
    assert coaching.optional_dimension_ids() == [4]
    assert coaching.max_possible(disabled_ids={4}) == 85
    assert coaching.max_possible() == 100

    kickoff = load_rubric(CallType.KICKOFF)
    assert kickoff.optional_dimension_ids() == []
    assert kickoff.max_possible(disabled_ids={4}) == 85  # kickoff D4 is not optional but max_possible is generic


def test_unknown_call_type_raises():
    """R7: a call type without a rubric mapping raises a clear error."""
    with pytest.raises(RubricParseError, match="rubric mapping"):
        load_rubric("webinar")  # type: ignore[arg-type]


def test_missing_file_raises(tmp_path):
    """R7: missing markdown file raises with the path in the message."""
    with pytest.raises(RubricParseError, match="not found"):
        load_rubric(CallType.COACHING, rubrics_dir=tmp_path)


def test_malformed_rubric_raises():
    """R8: unparseable point values abort the load with a parse error."""
    with pytest.raises(RubricParseError):
        load_rubric(CallType.COACHING, rubrics_dir=FIXTURES / "malformed")


def test_incomplete_rubric_raises():
    """R8: fewer than 12 dimensions is rejected, never partially built."""
    with pytest.raises(RubricParseError, match="12 dimensions"):
        load_rubric(CallType.COACHING, rubrics_dir=FIXTURES / "incomplete")
