# Tasks — rubric_loader

- [ ] T1 — Create `src/rubrics.py` with `Dimension`, `ScoreCap`, `Rubric` models. Covers: R2, R4, R5, R6.
- [ ] T2 — Implement markdown parser for dimensions, bands, caps and the optional marker. Covers: R1, R5, R8.
- [ ] T3 — Implement `load_rubric(call_type)` with path resolution and missing-file error. Covers: R1, R7.
- [ ] T4 — Implement `Rubric.max_possible(disabled_ids)` (85 with coaching D4 disabled). Covers: R6.
- [ ] T5 — Create `tests/fixtures/rubrics/` with valid, malformed and incomplete minimal rubrics. Covers: R8.
- [ ] T6 — Write `tests/test_rubrics.py::test_load_rubric_twelve_dimensions_sum_100` (both real rubrics). Covers: R1, R2, R3.
- [ ] T7 — Write `tests/test_rubrics.py::test_band_names_exact`. Covers: R4.
- [ ] T8 — Write `tests/test_rubrics.py::test_score_caps_exposed`. Covers: R5.
- [ ] T9 — Write `tests/test_rubrics.py::test_coaching_optional_d4_max_possible`. Covers: R6.
- [ ] T10 — Write `tests/test_rubrics.py::test_unknown_call_type_raises`. Covers: R7.
- [ ] T11 — Write `tests/test_rubrics.py::test_malformed_rubric_raises`. Covers: R8.
- [ ] T12 — Run `uv run pytest`; suite green. Covers: R1–R8.
