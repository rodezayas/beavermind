# Implementation — project_scaffold

## Traceability
- R1 → `test_settings_reads_all_variables`
- R2 → `test_config_missing_variable`, `test_config_empty_variable_is_missing`
- R3 → `test_call_type_and_status_values`
- R4 → `test_run_defaults_and_fields`
- R5 → `test_call_type_and_status_values`
- R6 → `test_failed_run_requires_error_reason`, `test_failed_run_with_reason_is_valid`
- R7 → `test_disabled_dimension_valid`
- R8 → `test_disabled_dimension_requires_reason`, `test_disabled_dimension_with_score_rejected`
- R9 → `test_report_requires_twelve_dimensions`, `test_valid_report_holds_twelve_dimensions`

## Tasks checklist (specs/project_scaffold/tasks.md)
- [x] T1 — src/config.py (ConfigError, Settings, get_settings)
- [x] T2 — src/schemas.py (CallType, RunStatus)
- [x] T3 — Run model + failed validator
- [x] T4 — DimensionScore + disabled rules
- [x] T5 — Grade + Report (12-dimension invariant)
- [x] T6–T10 — tests/test_schemas.py
- [x] T11 — `uv run pytest`: 12 passed

## Notes / deviations
- Added `[tool.pytest.ini_options] pythonpath = ["."]` to pyproject.toml so
  `src.*` is importable from the test suite (build infrastructure, not a spec
  deviation).
- Added `pydantic` as a direct dependency (approved set); it was only
  transitive via fastapi before, but we import it directly.
- `get_settings(environ=None)` accepts an injected mapping for tests instead of
  monkeypatching `os.environ`.
