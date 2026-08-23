"""Tests for src/config.py and src/schemas.py (feature: project_scaffold)."""

import pytest
from pydantic import ValidationError

from src.config import ConfigError, get_settings
from src.schemas import (
    CallType,
    DimensionScore,
    Grade,
    OneThing,
    Report,
    Run,
    RunStatus,
)

FULL_ENV = {
    "SUPABASE_PROJECT_ID": "proj",
    "SUPABASE_API_KEY": "anon-key",
    "SUPABASE_SECRET_KEY": "secret-key",
    "GROQ_API_KEY": "grog-key",
    "DATABASE": "postgres://localhost/db",
}


def _dimension(dimension_id: int = 1, **overrides) -> DimensionScore:
    """Build a valid scored dimension for report construction."""
    defaults = dict(
        dimension_id=dimension_id,
        name=f"Dimension {dimension_id}",
        max_points=10,
        score=7,
        band="Strong",
        reasoning="because",
        transcript_lines=["[A]: hi"],
        quick_fix="do X",
    )
    defaults.update(overrides)
    return DimensionScore(**defaults)


def _report(**overrides) -> Report:
    """Build a valid 12-dimension report for run construction."""
    defaults = dict(
        one_thing=OneThing(change="book live", projected_score=92),
        brief="Solid call.",
        red_flags=["no booking"],
        grade=Grade(total=78, band="Inconsistent"),
        dimensions=[_dimension(i) for i in range(1, 13)],
    )
    defaults.update(overrides)
    return Report(**defaults)


# --- R1 / R2: config -------------------------------------------------------


def test_settings_reads_all_variables():
    settings = get_settings(FULL_ENV)
    assert settings.groq_api_key == "grog-key"
    assert settings.database == "postgres://localhost/db"


def test_config_missing_variable():
    env = {k: v for k, v in FULL_ENV.items() if k != "GROQ_API_KEY"}
    with pytest.raises(ConfigError) as exc:
        get_settings(env)
    assert "GROQ_API_KEY" in str(exc.value)


def test_config_empty_variable_is_missing():
    with pytest.raises(ConfigError) as exc:
        get_settings({**FULL_ENV, "DATABASE": ""})
    assert "DATABASE" in str(exc.value)


# --- R3 / R5: enums --------------------------------------------------------


def test_call_type_and_status_values():
    assert {c.value for c in CallType} == {"kickoff", "coaching"}
    assert {s.value for s in RunStatus} == {
        "pending",
        "scoring",
        "completed",
        "failed",
    }


# --- R4 / R6: run ----------------------------------------------------------


def test_run_defaults_and_fields():
    run = Run(call_type=CallType.KICKOFF, transcript="[A]: hi\n[B]: hello")
    assert run.status is RunStatus.PENDING
    assert run.report is None
    assert run.run_id is not None
    assert run.created_at is not None


def test_failed_run_requires_error_reason():
    with pytest.raises(ValidationError, match="error_reason"):
        Run(
            call_type=CallType.COACHING,
            transcript="[A]: hi",
            status=RunStatus.FAILED,
        )


def test_failed_run_with_reason_is_valid():
    run = Run(
        call_type=CallType.COACHING,
        transcript="[A]: hi",
        status=RunStatus.FAILED,
        error_reason="transcript too short",
    )
    assert run.error_reason == "transcript too short"


# --- R7 / R8: dimension score ---------------------------------------------


def test_disabled_dimension_requires_reason():
    with pytest.raises(ValidationError, match="disabled_reason"):
        DimensionScore(
            dimension_id=4,
            name="Movement Coaching Quality",
            max_points=15,
            score=None,
            band=None,
            reasoning="n/a",
            quick_fix="n/a",
            disabled=True,
        )


def test_disabled_dimension_with_score_rejected():
    with pytest.raises(ValidationError, match="disabled"):
        DimensionScore(
            dimension_id=4,
            name="Movement Coaching Quality",
            max_points=15,
            score=10,
            band="Strong",
            reasoning="n/a",
            quick_fix="n/a",
            disabled=True,
            disabled_reason="no movement coaching",
        )


def test_disabled_dimension_valid():
    dim = DimensionScore(
        dimension_id=4,
        name="Movement Coaching Quality",
        max_points=15,
        score=None,
        band=None,
        reasoning="not applicable",
        quick_fix="n/a",
        disabled=True,
        disabled_reason="no movement coaching on this call",
    )
    assert dim.score is None


# --- R9: report ------------------------------------------------------------


def test_report_requires_twelve_dimensions():
    with pytest.raises(ValidationError, match="12"):
        _report(dimensions=[_dimension(i) for i in range(1, 11)])


def test_valid_report_holds_twelve_dimensions():
    report = _report()
    assert len(report.dimensions) == 12
    assert report.grade.band == "Inconsistent"
