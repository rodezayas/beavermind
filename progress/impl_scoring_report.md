# Implementation — scoring_report

## Traceability
- R1 → `test_build_report_valid`
- R2 → `test_score_above_max_rejected`, `test_negative_score_rejected`, `test_unknown_dimension_band_rejected`
- R3 → `test_missing_section_rejected` (parametrized), `test_missing_dimension_entry_rejected`, `test_unknown_dimension_id_rejected`
- R4 → `test_coaching_d4_disabled_max_85`, `test_non_optional_dimension_disabled_rejected`
- R5 → `test_band_thresholds_mapping` (10 thresholds), `test_grade_band_wiring`, `test_grade_band_on_85_scale_uses_percentage` (77/85 → Elite)
- R6 → `test_cap_limits_dimension_score`, `test_cap_not_fired_leaves_score_untouched`
- R7 → `test_projected_score_capped`
- R8 → `test_prompt_contains_rubric_and_json_contract`, `test_prompt_frames_transcript_as_untrusted` (agent's R13: verified here)

## Tasks checklist (specs/scoring_report/tasks.md)
- [x] T1–T14 completed; `uv run pytest`: 78 passed (full suite).

## Notes / decisions during implementation
- **Amendment to the design (R6, conditional caps)**: we discovered while testing that
  the rubric caps are conditional ("IF client struggle ignored THEN
  0/5 on D8") — applying them unconditionally nullified D8/D10 in every coaching
  report. The condition is semantic: now the LLM declares `cap_fired` per
  dimension and only then does the engine trim to the maximum and annotate it. Spec
  (requirements R6 + design) updated before final code.
- The grade (total + band) is computed 100% in code from the percentage
  (total/max_possible), complying with the rubric note "report the result
  on the 100 scale" when D4 is disabled.
- `ScoringValidationError` is a typed `ValueError` so the API can
  map it to a run failed with a clear cause.
