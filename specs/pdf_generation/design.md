# Design — pdf_generation

> Cómo se construye la feature 8. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/pdf_creation/__init__.py` | create | paquete (ya existe el dir) |
| `src/pdf_creation/report_pdf.py` | create | `PdfRenderError`, `render_pdf(report) -> bytes` |
| `tests/test_pdf.py` | create | cobertura R2–R7 |
| `pyproject.toml` | modify | agregar `fpdf2` (aprobada) |

## New signatures

```python
# src/pdf_creation/report_pdf.py
class PdfRenderError(ValueError): ...

def render_pdf(report: Report) -> bytes
```

## Layout (fpdf2)

- Portada compacta: título del reporte, call type implícito en el contenido,
  fecha, total + banda en tipografía destacada.
- Secciones en el orden de `pdf_format.md` (R2) con encabezados repetidos en
  cada página (`header()` del FPDF).
- Dimensiones como bloques: `D<n> — <name> — <score>/<max>`; debajo,
  Reasoning / Evidence (líneas citadas en itálica) / Quick fix.
- Fuente estándar Helvetica (fpdf2 core font) — evita empotrar TTFs; el
  contenido es inglés del reporte, sin necesidad de Unicode extendido.

## Decisions
- **fpdf2 puro, sin plantillas HTML** (weasyprint/pdfkit descartados): son
  dependencias pesadas con binarios del sistema; fpdf2 ya está en el stack
  aprobado y el layout del reporte es simple y secuencial.
- **`render_pdf` devuelve `bytes`** (no escribe archivos): la API (feature 7)
  lo sirve en memoria como respuesta HTTP; sin archivos temporales que
  limpiar.
- **Validación defensiva al inicio** (R6): reutiliza los validadores del
  modelo `Report` y agrega chequeos propios antes de dibujar.

## Alternative discarded
- ReportLab: descartado — API más verbosa, licencia dual confusa para el mismo
  resultado; fpdf2 cubre el caso con menos superficie.

## Traceability preview
- R1, R7 → `test_render_pdf_produces_valid_bytes`
- R2 → `test_pdf_contains_sections_in_order`
- R3 → `test_pdf_dimension_block_content`
- R4 → `test_pdf_band_uses_canonical_names`
- R5 → `test_pdf_disabled_dimension_shows_na`
- R6 → `test_render_rejects_invalid_report`
