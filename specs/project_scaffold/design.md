# Design — project_scaffold

> Cómo se construye la feature 1. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/config.py` | create | `Settings` (pydantic) + `get_settings()` cacheado |
| `src/schemas.py` | create | `CallType`, `RunStatus`, `Run`, `DimensionScore`, `Grade`, `Report` |
| `tests/test_schemas.py` | create | Cobertura de R2–R9 |
| `src/__init__.py`, `tests/__init__.py` | create | Paquetes importables |

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
class Run(BaseModel): ...             # model_validator: failed ⇒ error_reason no vacío (R6)
class DimensionScore(BaseModel): ...  # validator: disabled ⇒ score/band None + reason (R8)
class Grade(BaseModel): total: float; band: str; max_possible: float
class Report(BaseModel): ...          # validator: exactamente 12 dimensiones (R9)
```

## Exceptions
- `ConfigError(RuntimeError)` en `src/config.py` — mensaje nombra la variable faltante.

## Decisions
- **Pydantic v2** (ya en el stack aprobado): las reglas condicionales R6/R8 viven
  como validators en el modelo, no duplicadas en los llamadores.
- **StrEnum** para `CallType`/`RunStatus`: serializa a JSON y compara directo con
  los strings de la API sin capa de conversión.
- **Settings leyendo `os.getenv` manualmente** (sin `pydantic-settings`): solo
  hacen falta 5 variables; la dependencia extra no gana nada aquí.

## Alternative discarded
- `dataclasses` solo stdlib: descartada porque imponer R6/R8 exigiría
  `__post_init__` manual repetido en cada modelo; pydantic centraliza la
  validación y ya está aprobado en el stack.

## Traceability preview
- R2 → `test_config_missing_variable`
- R3, R5 → `test_call_type_and_status_values`
- R6 → `test_failed_run_requires_error_reason`
- R8 → `test_disabled_dimension_requires_reason`
- R9 → `test_report_requires_twelve_dimensions`
