# Design — project_scaffold

> How feature 1 is built. Decisions made before writing code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/config.py` | create | `Settings` (pydantic) + cached `get_settings()` |
| `src/schemas.py` | create | `CallType`, `RunStatus`, `Run`, `DimensionScore`, `Grade`, `Report` |
| `tests/test_schemas.py` | create | Coverage of R2–R9 |
| `src/__init__.py`, `tests/__init__.py` | create | Importable packages |

## New signatures

```python
# src/config.py
class Settings(BaseModel):
    supabase_project_id: str
    supabase_api_key: str
    supabase_secret_key: str
    groq_api_key: str
    database: str

def get_settings() -> Settings:  # cached; raises ConfigError naming the missing var

# src/schemas.py
class CallType(StrEnum): KICKOFF = "kickoff"; COACHING = "coaching"
class RunStatus(StrEnum): PENDING = "pending"; SCORING = "scoring"; COMPLETED = "completed"; FAILED = "failed"
class Run(BaseModel): ...             # model_validator: failed ⇒ non-empty error_reason (R6)
class DimensionScore(BaseModel): ...  # validator: disabled ⇒ None score/band + reason (R8)
class Grade(BaseModel): total: float; band: str; max_possible: float
class Report(BaseModel): ...          # validator: exactly 12 dimensions (R9)
```

## Exceptions
- `ConfigError(RuntimeError)` in `src/config.py` — the message names the missing variable.

## Decisions
- **Pydantic v2** (already in the approved stack): the conditional rules R6/R8 live
  as validators on the models, not duplicated in the callers.
- **StrEnum** for `CallType`/`RunStatus`: serializes to JSON and compares directly with
  the API strings without a conversion layer.
- **Settings reading `os.getenv` manually** (without `pydantic-settings`): only
  5 variables are needed; the extra dependency buys nothing here.

## Alternative discarded
- stdlib-only `dataclasses`: discarded because enforcing R6/R8 would require
  manual, repeated `__post_init__` in each model; pydantic centralizes the
  validation and is already approved in the stack.

## Traceability preview
- R2 → `test_config_missing_variable`
- R3, R5 → `test_call_type_and_status_values`
- R6 → `test_failed_run_requires_error_reason`
- R8 → `test_disabled_dimension_requires_reason`
- R9 → `test_report_requires_twelve_dimensions`
