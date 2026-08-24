# Tasks — pdf_generation

- [x] T1 — Add `fpdf2` dependency (approved set). Covers: R1.
- [x] T2 — Create `src/pdf_creation/report_pdf.py` with `PdfRenderError` and `render_pdf()`. Covers: R1, R6.
- [x] T3 — Render sections in pdf_format.md order (one thing, brief, red flags, grade, dimensions). Covers: R2.
- [x] T4 — Render each dimension block: score/max, reasoning, evidence lines, quick fix. Covers: R3.
- [x] T5 — Render disabled dimensions as N/A with reason. Covers: R5.
- [x] T6 — Write `test_render_pdf_produces_valid_bytes` (%PDF header). Covers: R1, R7.
- [x] T7 — Write `test_pdf_contains_sections_in_order`. Covers: R2.
- [x] T8 — Write `test_pdf_dimension_block_content`. Covers: R3.
- [x] T9 — Write `test_pdf_band_uses_canonical_names`. Covers: R4.
- [x] T10 — Write `test_pdf_disabled_dimension_shows_na`. Covers: R5.
- [x] T11 — Write `test_render_rejects_invalid_report`. Covers: R6.
- [x] T12 — Run `uv run pytest`; suite green. Covers: R1–R7.
