# Implementation — pdf_generation

## Traceability
- R1, R7 → `test_render_pdf_produces_valid_bytes` (bytes + `%PDF` header)
- R2 → `test_pdf_contains_sections_in_order` (4 secciones + 12 dims, orden de pdf_format.md), `test_one_thing_includes_projected_score`
- R3 → `test_pdf_dimension_block_content` (score/max, reasoning, evidencia, quick fix)
- R4 → `test_pdf_band_uses_canonical_names` (78 / 100 - Inconsistent)
- R5 → `test_pdf_disabled_dimension_shows_na`
- R6 → `test_render_rejects_invalid_report`, `test_render_rejects_wrong_dimension_count`, `test_render_rejects_empty_band`
- R7 (extra) → `test_render_survives_unicode_content`, `test_report_from_either_call_type_renders`

## Tasks checklist (specs/pdf_generation/tasks.md)
- [x] T1–T12 completados; `uv run pytest`: 101 passed.

## Notes / decisions during implementation
- El contenido se ensambla primero en `build_sections(report)` (lista de
  pares heading/body) y luego se dibuja: así el orden y contenido son
  verificables sin un extractor de texto de PDF (evita la dependencia
  `pypdf`, no aprobada).
- fpdf2 core fonts son latin-1: `_safe()` reemplaza caracteres fuera de
  rango (em-dashes, acentos) para que el render nunca falle por encoding.
- fpdf2 `multi_cell` deja el cursor a la derecha por defecto; se fija
  `new_x="LMARGIN", new_y="NEXT"` en cada llamada.
- `PdfRenderError` valida estructura ANTES de dibujar: nunca produce un PDF
  corrupto.
