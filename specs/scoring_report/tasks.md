# Tasks — scoring_report

- [ ] T1 — Create `src/scoring.py` with `ScoringValidationError` and `build_prompt()`. Covers: R8.
- [ ] T2 — Implement `build_report()`: parse sections, reject missing ones. Covers: R1, R3.
- [ ] T3 — Validate per-dimension scores and band labels against the rubric. Covers: R2.
- [ ] T4 — Handle optional dimension (D4 disabled → max 85). Covers: R4.
- [ ] T5 — Compute grade locally from thresholds (Scoring Bands Reference). Covers: R5.
- [ ] T6 — Apply global automatic score caps and annotate the fired cap. Covers: R6.
- [ ] T7 — Bound `one_thing.projected_score` to `max_possible`. Covers: R7.
- [ ] T8 — Write `test_build_report_valid` and `test_missing_section_rejected`. Covers: R1, R3.
- [ ] T9 — Write `test_score_above_max_rejected` and `test_unknown_dimension_band_rejected`. Covers: R2.
- [ ] T10 — Write `test_coaching_d4_disabled_max_85`. Covers: R4.
- [ ] T11 — Write `test_grade_band_from_thresholds`. Covers: R5.
- [ ] T12 — Write `test_cap_limits_dimension_score` and `test_projected_score_capped`. Covers: R6, R7.
- [ ] T13 — Write `test_prompt_contains_rubric_and_json_contract`. Covers: R8.
- [ ] T14 — Run `uv run pytest`; suite green. Covers: R1–R8.
