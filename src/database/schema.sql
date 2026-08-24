-- Scoring system schema (Supabase / PostgreSQL).
-- The `beaverops` table is the single source of truth: every run is
-- addressable by its run_id (the public URL id) and survives across sessions
-- and deploys. Access is service-role only from the backend; no client-facing
-- policies.
--
-- NOTE: the live table names its update timestamp `updatet_at` (typo included)
-- and types it as timestamp without time zone; the repository maps that column
-- to the domain field `updated_at`. The DDL below mirrors the live table.

create table if not exists beaverops (
  run_id uuid primary key default gen_random_uuid(),
  call_type text not null,
  status text not null,
  transcript text not null,
  report jsonb,
  error_reason text,
  created_at timestamptz not null default now(),
  updatet_at timestamp not null default now()
);
