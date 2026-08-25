# Implementation — rubric_loader

## Traceability
- R1, R2, R3 → `test_load_rubric_twelve_dimensions_sum_100` (both real rubrics)
- R4 → `test_band_names_exact`
- R5 → `test_score_caps_exposed`, `test_coaching_d6_adjusted_cap_exposed`
- R6 → `test_coaching_optional_d4_max_possible`
- R7 → `test_unknown_call_type_raises`, `test_missing_file_raises`
- R8 → `test_malformed_rubric_raises`, `test_incomplete_rubric_raises`

## Tasks checklist (specs/rubric_loader/tasks.md)
- [x] T1 — `src/rubrics.py`: Dimension, ScoreCap, Rubric
- [x] T2 — markdown parser (dimensions, bands, caps, optional marker)
- [x] T3 — `load_rubric(call_type)` with missing-file error
- [x] T4 — `Rubric.max_possible(disabled_ids)`
- [x] T5 — valid/malformed/incomplete fixtures
- [x] T6–T11 — tests/test_rubrics.py
- [x] T12 — `uv run pytest`: 21 passed (full suite)

## Notes / deviations (approved by the human during implementation)
- **Inconsistent data in the coaching rubric**: it added up to 105 while declaring 100.
  Human decision: adjust to exactly 100 (D6 15→10) and document in the README.
  Recorded in `docs/ADR.md` and `README.md`.
- The kick-off cap uses "Dimension 4" (full word) instead of "D4"; the
  parser accepts both forms.
- Pydantic validation errors are re-wrapped in `RubricParseError`
  so that the public API exposes a single parsing error type.
- ScoreCap supports dimension caps (`max_dimension_score`) and total caps
  (`max_total`, e.g. "Max 75 total") because the rubric declares both types.
