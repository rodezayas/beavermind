# Implementation — pdf_generation

## Traceability
- R1, R7 → `test_render_pdf_produces_valid_bytes` (bytes + `%PDF` header)
- R2 → `test_pdf_contains_sections_in_order` (4 sections + 12 dims, order from pdf_format.md), `test_one_thing_includes_projected_score`
- R3 → `test_pdf_dimension_block_content` (score/max, reasoning, evidence, quick fix)
- R4 → `test_pdf_band_uses_canonical_names` (78 / 100 - Inconsistent)
- R5 → `test_pdf_disabled_dimension_shows_na`
- R6 → `test_render_rejects_invalid_report`, `test_render_rejects_wrong_dimension_count`, `test_render_rejects_empty_band`
- R7 (extra) → `test_render_survives_unicode_content`, `test_report_from_either_call_type_renders`

## Tasks checklist (specs/pdf_generation/tasks.md)
- [x] T1–T12 completed; `uv run pytest`: 101 passed.

## Notes / decisions during implementation
- Content is assembled first in `build_sections(report)` (list of
  heading/body pairs) and then drawn: this way the order and content are
  verifiable without a PDF text extractor (avoids the `pypdf`
  dependency, not approved).
- fpdf2 core fonts are latin-1: `_safe()` replaces characters outside
  range (em-dashes, accented characters) so rendering never fails due to encoding.
- fpdf2 `multi_cell` leaves the cursor on the right by default;
  `new_x="LMARGIN", new_y="NEXT"` is set on each call.
- `PdfRenderError` validates structure BEFORE drawing: it never produces a corrupt PDF.
