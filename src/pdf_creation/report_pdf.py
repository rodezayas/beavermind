"""PDF rendering of scoring reports (fpdf2).

`render_pdf` turns a validated `Report` into PDF bytes following the section
order of `pdf_format.md`. The content is assembled as a section list first
(testable without a PDF parser) and then drawn.
"""

from fpdf import FPDF

from src.schemas import Report

#: Error raised when the report cannot be rendered safely
PdfRenderError = ValueError


class PdfRenderError(ValueError):
    """Raised when the report is invalid for rendering (never a corrupt PDF)."""


def _safe(text: str) -> str:
    """Make text safe for fpdf2 core fonts (latin-1), replacing extras."""
    return (text or "").encode("latin-1", errors="replace").decode("latin-1")


def _dimension_line(report: Report, index: int) -> tuple[str, list[str]]:
    """Build the heading and body lines for one dimension block (R3, R5)."""
    dim = report.dimensions[index]
    if dim.disabled:
        heading = f"D{dim.dimension_id} - {dim.name} - N/A"
        body = [
            f"Disabled: {dim.disabled_reason}",
            f"Quick fix: {dim.quick_fix}",
        ]
        return heading, body
    heading = f"D{dim.dimension_id} - {dim.name} - {dim.score:g}/{dim.max_points}"
    body = [
        f"Band: {dim.band}",
        f"Reasoning: {dim.reasoning}",
        *[f'Evidence: "{line}"' for line in dim.transcript_lines],
        f"Quick fix: {dim.quick_fix}",
    ]
    return heading, body


def build_sections(report: Report) -> list[tuple[str, list[str]]]:
    """Assemble the report content as ordered (heading, body lines) pairs.

    The order mirrors pdf_format.md (R2): the one thing, the brief, red
    flags, grade and total, then the twelve dimensions. Kept separate from
    drawing so the content is verifiable without a PDF text extractor.
    """
    sections: list[tuple[str, list[str]]] = [
        (
            "The one thing",
            [
                f"Change: {report.one_thing.change}",
                f"Projected score with it applied: {report.one_thing.projected_score:g}"
                f" (now {report.grade.total:g})",
            ],
        ),
        ("The brief", [report.brief]),
    ]
    if report.red_flags:
        sections.append(
            ("Red flags", [f"- {flag}" for flag in report.red_flags])
        )
    else:
        sections.append(("Red flags", ["None detected."]))
    sections.append(
        (
            "Grade and total",
            [f"{report.grade.total:g} / {report.grade.max_possible:g}"
             f" - {report.grade.band}"],
        )
    )
    for index in range(len(report.dimensions)):
        heading, body = _dimension_line(report, index)
        sections.append((heading, body))
    return sections


def _draw(pdf: FPDF, heading: str, body: list[str]) -> None:
    """Draw one section: a bold heading and its body lines."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 7, text=_safe(heading), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for line in body:
        pdf.multi_cell(0, 5, text=_safe(line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def render_pdf(report: Report) -> bytes:
    """Render the report to PDF bytes.

    Args:
        report: A completed scoring report.

    Returns:
        The PDF file content as bytes.

    Raises:
        PdfRenderError: If the report is structurally invalid; never returns
            a corrupt PDF.
    """
    if not isinstance(report, Report):
        raise PdfRenderError("render_pdf expects a Report instance")
    if len(report.dimensions) != 12:
        raise PdfRenderError(
            f"report must have 12 dimensions to render, got {len(report.dimensions)}"
        )
    if not report.grade.band:
        raise PdfRenderError("report grade band is empty")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, text="Call Scoring Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for heading, body in build_sections(report):
        _draw(pdf, heading, body)
    return bytes(pdf.output())


__all__ = ["PdfRenderError", "build_sections", "render_pdf"]
