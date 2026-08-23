# Implementation — rubric_loader

## Traceability
- R1, R2, R3 → `test_load_rubric_twelve_dimensions_sum_100` (ambas rúbricas reales)
- R4 → `test_band_names_exact`
- R5 → `test_score_caps_exposed`, `test_coaching_d6_adjusted_cap_exposed`
- R6 → `test_coaching_optional_d4_max_possible`
- R7 → `test_unknown_call_type_raises`, `test_missing_file_raises`
- R8 → `test_malformed_rubric_raises`, `test_incomplete_rubric_raises`

## Tasks checklist (specs/rubric_loader/tasks.md)
- [x] T1 — `src/rubrics.py`: Dimension, ScoreCap, Rubric
- [x] T2 — parser markdown (dimensiones, bandas, caps, marcador opcional)
- [x] T3 — `load_rubric(call_type)` con error de archivo faltante
- [x] T4 — `Rubric.max_possible(disabled_ids)`
- [x] T5 — fixtures valid/malformed/incomplete
- [x] T6–T11 — tests/test_rubrics.py
- [x] T12 — `uv run pytest`: 21 passed (suite completa)

## Notes / deviations (aprobadas por el humano durante la implementación)
- **Dato inconsistente en la rúbrica coaching**: sumaba 105 declarando 100.
  Decisión del humano: ajustar a 100 exacto (D6 15→10) y documentar en README.
  Registrado en `docs/ADR.md` y `README.md`.
- El cap de kick-off usa "Dimension 4" (palabra completa) en vez de "D4"; el
  parser acepta ambas formas.
- Los errores de validación de pydantic se re-envuelven en `RubricParseError`
  para que la API pública exponga un único tipo de error de parseo.
- ScoreCap soporta caps de dimensión (`max_dimension_score`) y caps de total
  (`max_total`, p.ej. "Max 75 total") porque la rúbrica declara ambos tipos.
