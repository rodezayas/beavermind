# Design — pdf_generation

> How feature 8 is built. Decisions made before writing code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/pdf_creation/__init__.py` | create | package (dir already exists) |
| `src/pdf_creation/report_pdf.py` | create | `PdfRenderError`, `render_pdf(report) -> bytes` |
| `tests/test_pdf.py` | create | R2–R7 coverage |
| `pyproject.toml` | modify | add `fpdf2` (approved) |

## New signatures

```python
# src/pdf_creation/report_pdf.py
class PdfRenderError(ValueError): ...

def render_pdf(report: Report) -> bytes
```

## Layout (fpdf2)

- Compact cover: report title, call type implied by the content,
  date, total + band in prominent typography.
- Sections in the order of `pdf_format.md` (R2) with repeated headers on
  each page (the FPDF `header()`).
- Dimensions as blocks: `D<n> — <name> — <score>/<max>`; below that,
  Reasoning / Evidence (quoted lines in italics) / Quick fix.
- Standard Helvetica font (fpdf2 core font) — avoids embedding TTFs; the
  content is English from the report, no extended Unicode needed.

## Decisions
- **Pure fpdf2, no HTML templates** (weasyprint/pdfkit discarded): they are
  heavy dependencies with system binaries; fpdf2 is already in the approved
  stack and the report layout is simple and sequential.
- **`render_pdf` returns `bytes`** (does not write files): the API (feature 7)
  serves it in memory as an HTTP response; no temporary files to clean up.
- **Defensive validation up front** (R6): reuses the validators from the
  `Report` model and adds its own checks before drawing.

## Alternative discarded
- ReportLab: discarded — more verbose API, confusing dual license for the same
  result; fpdf2 covers the case with a smaller surface.

## Traceability preview
- R1, R7 → `test_render_pdf_produces_valid_bytes`
- R2 → `test_pdf_contains_sections_in_order`
- R3 → `test_pdf_dimension_block_content`
- R4 → `test_pdf_band_uses_canonical_names`
- R5 → `test_pdf_disabled_dimension_shows_na`
- R6 → `test_render_rejects_invalid_report`
