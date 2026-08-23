# Design — database_supabase

> Cómo se construye la feature 6. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/database/__init__.py` | create | paquete |
| `src/database/schema.sql` | create | DDL de la tabla `runs` |
| `src/database/repository.py` | create | `RepositoryError`, `RunRepository`, `SupabaseRunRepository`, `InMemoryRunRepository` |
| `tests/test_database.py` | create | cobertura R2–R8 contra `InMemoryRunRepository` |
| `pyproject.toml` | modify | agregar `supabase` (aprobada) |

## Schema (schema.sql)

```sql
create table if not exists runs (
  run_id uuid primary key,
  call_type text not null check (call_type in ('kickoff', 'coaching')),
  status text not null check (status in ('pending','scoring','completed','failed')),
  transcript text not null,
  report jsonb,
  error_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

RLS: el acceso será service-role desde el backend (secret key en Settings);
ninguna clave va al cliente.

## New signatures

```python
class RepositoryError(RuntimeError):
    def __init__(self, message: str, run_id: UUID | None = None, cause: Exception | None = None)

class RunRepository(Protocol):
    def create(self, run: Run) -> Run: ...
    def get(self, run_id: UUID) -> Run | None: ...
    def update(self, run: Run) -> Run: ...

class SupabaseRunRepository:  # construido con (client: Client)
class InMemoryRunRepository:  # dict interno, para tests/dev
```

Serialización: `Run.model_dump(mode="json")` ↔ `Run.model_validate(row)` —
una sola fuente de verdad para el formato de fila.

## Decisions
- **Protocolo `RunRepository` + dos implementaciones**: la API y el agente
  dependen del protocolo; Supabase es un detalle. Los tests corren con
  `InMemoryRunRepository` sin red ni credenciales.
- **`report` como jsonb**: el reporte se consulta completo por run_id (nunca
  por campos internos), así que no hace falta normalizar las 12 dimensiones.
- **`updated_at` lo toca el repository en cada `update`** (R7), no el modelo.

## Alternative discarded
- SQLite local: descartado porque el requisito de negocio exige que la URL del
  run siga funcionando "next week" desde cualquier proceso/despliegue — se
  necesita almacenamiento administrado compartido (Supabase, ya en el stack).

## Traceability preview
- R1 → revisión de `schema.sql` + `test_roundtrip_preserves_all_fields`
- R2, R4 → `test_in_memory_repository_roundtrip`
- R5 → `test_create_returns_run`
- R6 → `test_get_missing_returns_none`
- R7 → `test_update_persists_failure_with_reason`, `test_update_refreshes_updated_at`
- R8 → `test_repository_error_wraps_cause`
- R9 → decisión estructural (protocolo + persistencia única); verificación en e2e
