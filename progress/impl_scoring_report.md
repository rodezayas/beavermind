# Implementation — scoring_report

## Traceability
- R1 → `test_build_report_valid`
- R2 → `test_score_above_max_rejected`, `test_negative_score_rejected`, `test_unknown_dimension_band_rejected`
- R3 → `test_missing_section_rejected` (parametrizado), `test_missing_dimension_entry_rejected`, `test_unknown_dimension_id_rejected`
- R4 → `test_coaching_d4_disabled_max_85`, `test_non_optional_dimension_disabled_rejected`
- R5 → `test_band_thresholds_mapping` (10 límites), `test_grade_band_wiring`, `test_grade_band_on_85_scale_uses_percentage` (77/85 → Elite)
- R6 → `test_cap_limits_dimension_score`, `test_cap_not_fired_leaves_score_untouched`
- R7 → `test_projected_score_capped`
- R8 → `test_prompt_contains_rubric_and_json_contract`, `test_prompt_frames_transcript_as_untrusted` (R13 del agente: verificada aquí)

## Tasks checklist (specs/scoring_report/tasks.md)
- [x] T1–T14 completados; `uv run pytest`: 78 passed (suite completa).

## Notes / decisions during implementation
- **Enmienda al design (R6, caps condicionales)**: descubrimos al testear que
  los caps de la rúbrica son condicionales ("IF client struggle ignored THEN
  0/5 on D8") — aplicarlos incondicionalmente anulaba D8/D10 en todo reporte
  coaching. La condición es semántica: ahora el LLM declara `cap_fired` por
  dimensión y el motor solo entonces recorta al máximo y lo anota. Spec
  (requirements R6 + design) actualizado antes del código final.
- El grade (total + banda) se calcula 100% en código sobre el porcentaje
  (total/max_possible), cumpliendo la nota de la rúbrica "report the result
  on the 100 scale" cuando D4 está deshabilitada.
- `ScoringValidationError` es un `ValueError` tipado para que la API pueda
  mapearlo a un run failed con causa clara.
