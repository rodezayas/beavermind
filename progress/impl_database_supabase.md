# Implementation — database_supabase

## Traceability
- R1 → `test_schema_sql_defines_runs_table`
- R2 → `test_in_memory_repository_roundtrip` (protocolo compartido por ambas implementaciones)
- R3 → `SupabaseRunRepository` + `test_supabase_repository_roundtrip_with_fake_client`
- R4 → `test_in_memory_repository_roundtrip`
- R5 → `test_create_returns_run`
- R6 → `test_get_missing_returns_none`
- R7 → `test_update_persists_failure_with_reason`, `test_update_persists_completed_report`, `test_update_refreshes_updated_at`
- R8 → `test_repository_error_wraps_cause` (run_id + causa + mensaje)
- R9 → decisión estructural: el dict en memoria nunca es fuente de verdad en producción; verificación final en `tests_e2e`

## Tasks checklist (specs/database_supabase/tasks.md)
- [x] T1–T10 completados; `uv run pytest`: 90 passed.

## Notes / decisions during implementation
- `SupabaseRunRepository` recibe el cliente inyectado (patrón DI del proyecto):
  los tests usan un fake con el mismo contrato `.table()` — sin red.
- `update` refresca `updated_at` en el repository (no en el modelo), como
  establece el design; `get` devuelve copias para evitar aliasing.
- `create` duplicado y `update` de run inexistente → `RepositoryError`
  explícito (fail-fast, sin upserts silenciosos).
