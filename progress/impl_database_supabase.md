# Implementation — database_supabase

## Traceability
- R1 → `test_schema_sql_defines_runs_table`
- R2 → `test_in_memory_repository_roundtrip` (protocol shared by both implementations)
- R3 → `SupabaseRunRepository` + `test_supabase_repository_roundtrip_with_fake_client`
- R4 → `test_in_memory_repository_roundtrip`
- R5 → `test_create_returns_run`
- R6 → `test_get_missing_returns_none`
- R7 → `test_update_persists_failure_with_reason`, `test_update_persists_completed_report`, `test_update_refreshes_updated_at`
- R8 → `test_repository_error_wraps_cause` (run_id + cause + message)
- R9 → structural decision: the in-memory dict is never the source of truth in production; final verification in `tests_e2e`

## Tasks checklist (specs/database_supabase/tasks.md)
- [x] T1–T10 completed; `uv run pytest`: 90 passed.

## Notes / decisions during implementation
- `SupabaseRunRepository` receives the injected client (project DI pattern):
  tests use a fake with the same `.table()` contract — no network.
- `update` refreshes `updated_at` in the repository (not in the model), as
  established by the design; `get` returns copies to avoid aliasing.
- Duplicate `create` and `update` of a nonexistent run → explicit `RepositoryError`
  (fail-fast, no silent upserts).
