# Requirements — database_supabase

> Feature 6 de `settings_files_tasks.json`. Estado: `spec_ready` (esperando aprobación humana).

## R1
The system MUST define the storage schema in `src/database/schema.sql`: a
`runs` table with `run_id` (uuid, primary key), `call_type`, `status`,
`transcript` (text), `report` (jsonb, nullable), `error_reason` (text,
nullable), `created_at` and `updated_at` (timestamptz).

## R2
The system MUST expose a `RunRepository` protocol in
`src/database/repository.py` with methods `create`, `get`, `update` so the
storage backend is swappable.

## R3
The system MUST implement `SupabaseRunRepository` against the `runs` table
using the approved `supabase` client and the credentials from `Settings`.

## R4
The system MUST implement `InMemoryRunRepository` with identical behavior for
tests and local development.

## R5
`create(run: Run) -> Run` MUST persist the run and return it unchanged.

## R6
`get(run_id: UUID) -> Run | None` MUST return the stored run or `None` when
the id does not exist (never raise for a missing id).

## R7
`update(run: Run) -> Run` MUST persist status transitions, a completed
report, or a failure with its `error_reason`, and refresh `updated_at`.

## R8
IF a storage operation fails (connection, constraint, permission) THEN the
repository MUST raise a `RepositoryError` that includes the underlying cause
and the `run_id` involved.

## R9
The repository layer MUST be the only source of truth on disk: no in-process
cache may be required for a run to be retrievable in a later process (the run
URL keeps working next week).
