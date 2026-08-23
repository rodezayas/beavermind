# Tasks — project_scaffold

- [ ] T1 — Create `src/__init__.py`, `src/config.py` with `ConfigError`, `Settings`, `get_settings()`. Covers: R1, R2.
- [ ] T2 — Create `src/schemas.py` with `CallType` and `RunStatus`. Covers: R3, R5.
- [ ] T3 — Add `Run` model with `model_validator` for failed-without-reason. Covers: R4, R6.
- [ ] T4 — Add `DimensionScore` model with disabled-dimension rules. Covers: R7, R8.
- [ ] T5 — Add `Grade` and `Report` models with the 12-dimension invariant. Covers: R9.
- [ ] T6 — Write `tests/test_schemas.py::test_config_missing_variable`. Covers: R2.
- [ ] T7 — Write `tests/test_schemas.py::test_call_type_and_status_values`. Covers: R3, R5.
- [ ] T8 — Write `tests/test_schemas.py::test_failed_run_requires_error_reason`. Covers: R6.
- [ ] T9 — Write `tests/test_schemas.py::test_disabled_dimension_requires_reason`. Covers: R8.
- [ ] T10 — Write `tests/test_schemas.py::test_report_requires_twelve_dimensions`. Covers: R9.
- [ ] T11 — Run `uv run pytest`; suite green. Covers: R1–R9.
