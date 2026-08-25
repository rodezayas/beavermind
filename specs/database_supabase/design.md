# Design — database_supabase

> How feature 6 is built. Decisions made before writing any code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/database/__init__.py` | create | package |
| `src/database/schema.sql` | create | DDL for the `runs` table |
| `src/database/repository.py` | create | `RepositoryError`, `RunRepository`, `SupabaseRunRepository`, `InMemoryRunRepository` |
| `tests/test_database.py` | create | covers R2–R8 against `InMemoryRunRepository` |
| `pyproject.toml` | modify | add `supabase` (approved) |

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

RLS: access will be service-role from the backend (secret key in Settings);
no key goes to the client.

## New signatures

```python
class RepositoryError(RuntimeError):
    def __init__(self, message: str, run_id: UUID | None = None, cause: Exception | None = None)

class RunRepository(Protocol):
    def create(self, run: Run) -> Run: ...
    def get(self, run_id: UUID) -> Run | None: ...
    def update(self, run: Run) -> Run: ...

class SupabaseRunRepository:  # built with (client: Client)
class InMemoryRunRepository:  # internal dict, for tests/dev
```

Serialization: `Run.model_dump(mode="json")` ↔ `Run.model_validate(row)` —
a single source of truth for the row format.

## Decisions
- **`RunRepository` protocol + two implementations**: the API and the agent
  depend on the protocol; Supabase is a detail. Tests run with
  `InMemoryRunRepository` without network or credentials.
- **`report` as jsonb**: the report is fetched whole by run_id (never by
  internal fields), so there is no need to normalize the 12 dimensions.
- **`updated_at` is touched by the repository at each `update`** (R7), not by the model.

## Alternative discarded
- Local SQLite: discarded because the business requirement demands that the run
  URL keeps working "next week" from any process/deployment — shared managed
  storage is needed (Supabase, already in the stack).

## Traceability preview
- R1 → review of `schema.sql` + `test_roundtrip_preserves_all_fields`
- R2, R4 → `test_in_memory_repository_roundtrip`
- R5 → `test_create_returns_run`
- R6 → `test_get_missing_returns_none`
- R7 → `test_update_persists_failure_with_reason`, `test_update_refreshes_updated_at`
- R8 → `test_repository_error_wraps_cause`
- R9 → structural decision (protocol + single persistence); verified in e2e
