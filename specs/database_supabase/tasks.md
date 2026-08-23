# Tasks — database_supabase

- [ ] T1 — Add `supabase` dependency (approved set). Covers: R3.
- [ ] T2 — Create `src/database/schema.sql` with the `runs` table DDL. Covers: R1.
- [ ] T3 — Create `src/database/repository.py` with `RepositoryError` and the `RunRepository` protocol. Covers: R2, R8.
- [ ] T4 — Implement `InMemoryRunRepository`. Covers: R4, R5, R6, R7.
- [ ] T5 — Implement `SupabaseRunRepository` over the supabase client. Covers: R3, R5, R6, R7, R8.
- [ ] T6 — Write `test_in_memory_repository_roundtrip` and `test_roundtrip_preserves_all_fields`. Covers: R2, R4, R9.
- [ ] T7 — Write `test_create_returns_run` and `test_get_missing_returns_none`. Covers: R5, R6.
- [ ] T8 — Write `test_update_persists_failure_with_reason` and `test_update_refreshes_updated_at`. Covers: R7.
- [ ] T9 — Write `test_repository_error_wraps_cause` (failing transport inyectado). Covers: R8.
- [ ] T10 — Run `uv run pytest`; suite green. Covers: R1–R8.
