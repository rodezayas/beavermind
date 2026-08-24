"""Tests for src/pdf_creation/report_pdf.py (feature: pdf_generation)."""

import pytest

from src.pdf_creation.report_pdf import PdfRenderError, build_sections, render_pdf
from src.schemas import (
    CallType,
    DimensionScore,
    Grade,
    OneThing,
    Report,
)


def _dimension(dimension_id: int = 1, **overrides) -> DimensionScore:
    defaults = dict(
        dimension_id=dimension_id,
        name=f"Dimension {dimension_id}",
        max_points=5,
        score=4,
        band="Strong",
        reasoning="quote-first rationale",
        transcript_lines=["[Coach]: great push"],
        quick_fix="ask the reflective question",
    )
    defaults.update(overrides)
    return DimensionScore(**defaults)


def _report(**overrides) -> Report:
    defaults = dict(
        one_thing=OneThing(change="book the next call live", projected_score=92),
        brief="A strong call with a weak close.",
        red_flags=["client never booked", "no accountability anchor"],
        grade=Grade(total=78, band="Inconsistent"),
        dimensions=[_dimension(i) for i in range(1, 13)],
    )
    defaults.update(overrides)
    return Report(**defaults)


# --- R1 / R7: valid bytes ----------------------------------------------------


def test_render_pdf_produces_valid_bytes():
    pdf_bytes = render_pdf(_report())
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


# --- R2: sections in order ---------------------------------------------------


def test_pdf_contains_sections_in_order():
    headings = [heading for heading, _ in build_sections(_report())]
    assert headings[:4] == [
        "The one thing",
        "The brief",
        "Red flags",
        "Grade and total",
    ]
    assert len(headings) == 16  # 4 sections + 12 dimensions
    assert headings[4].startswith("D1")
    assert headings[-1].startswith("D12")


def test_one_thing_includes_projected_score():
    sections = dict(build_sections(_report()))
    body = sections["The one thing"]
    assert any("92" in line for line in body)
    assert any("book the next call live" in line for line in body)


# --- R3: dimension block content --------------------------------------------


def test_pdf_dimension_block_content():
    sections = dict(build_sections(_report()))
    heading, body = next(
        (h, b) for h, b in sections.items() if h.startswith("D1 ")
    )
    assert "4/5" in heading
    assert any("quote-first rationale" in line for line in body)
    assert any('[Coach]: great push' in line for line in body)
    assert any("ask the reflective question" in line for line in body)


# --- R4: canonical band names ------------------------------------------------


def test_pdf_band_uses_canonical_names():
    sections = dict(build_sections(_report()))
    body = sections["Grade and total"]
    assert any("Inconsistent" in line for line in body)
    assert any("78 / 100" in line for line in body)


# --- R5: disabled dimensions -------------------------------------------------


def test_pdf_disabled_dimension_shows_na():
    dims = [
        _dimension(4, score=None, band=None, disabled=True,
                   disabled_reason="no movement coaching")
        if i == 4
        else _dimension(i)
        for i in range(1, 13)
    ]
    sections = dict(build_sections(_report(dimensions=dims)))
    heading, body = next(
        (h, b) for h, b in sections.items() if h.startswith("D4 ")
    )
    assert "N/A" in heading
    assert any("no movement coaching" in line for line in body)


# --- R6: invalid reports rejected -------------------------------------------


def test_render_rejects_invalid_report():
    with pytest.raises(PdfRenderError):
        render_pdf("not a report")  # type: ignore[arg-type]


def test_render_rejects_wrong_dimension_count():
    # model_construct bypasses the model validator to reach the render guard.
    bad = _report().model_construct(dimensions=[_dimension(i) for i in range(1, 11)])
    with pytest.raises(PdfRenderError, match="12 dimensions"):
        render_pdf(bad)


def test_render_rejects_empty_band():
    bad = _report(grade=Grade(total=78, band=""))
    with pytest.raises(PdfRenderError, match="band"):
        render_pdf(bad)


def test_render_survives_unicode_content():
    unicode_report = _report(brief="Coach used an em-dash — and a café.")
    pdf_bytes = render_pdf(unicode_report)  # must not raise
    assert pdf_bytes.startswith(b"%PDF")


# --- call type smoke (both rubric shapes render) -----------------------------


def test_report_from_either_call_type_renders():
    assert render_pdf(_report()).startswith(b"%PDF")
    dims = [
        _dimension(4, score=None, band=None, disabled=True,
                   disabled_reason="no movement")
        if i == 4
        else _dimension(i)
        for i in range(1, 13)
    ]
    assert render_pdf(_report(dimensions=dims)).startswith(b"%PDF")
