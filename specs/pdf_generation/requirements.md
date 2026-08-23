# Requirements — pdf_generation

> Feature 8 de `settings_files_tasks.json`. Estado: `spec_ready` (esperando aprobación humana).

## R1
The system MUST expose `render_pdf(report: Report) -> bytes` in
`src/pdf_creation/report_pdf.py`, built with `fpdf2`.

## R2
The PDF MUST contain the sections in the order defined by `pdf_format.md`:
1. The one thing (with the projected score if applied)
2. The brief
3. Red flags
4. A grade and a total (score + band)
5. The twelve dimensions

## R3
Each dimension section MUST show: its score over its maximum, the reasoning,
the transcript lines the reasoning rests on, and the quick fix.

## R4
The grade band MUST be printed with the rubric's canonical band names
(Elite, Strong, Inconsistent, At risk, Fail).

## R5
WHEN a dimension is disabled (optional, e.g. coaching D4) THEN the PDF MUST
show it as "N/A" with its `disabled_reason` instead of a score.

## R6
IF the report is invalid (missing sections, dimension count ≠ 12, disabled
dimension with score) THEN `render_pdf` MUST raise `PdfRenderError` naming
the problem instead of producing a corrupt PDF.

## R7
The produced bytes MUST start with the `%PDF` magic header and MUST be
text-extractable (section titles findable) so the content is verifiable.
