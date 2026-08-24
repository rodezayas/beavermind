-- Scoring system schema (Supabase / PostgreSQL).
-- The `runs` table is the single source of truth: every run is addressable by
-- its run_id (the public URL id) and survives across sessions and deploys.
-- Access is service-role only from the backend; no client-facing policies.

create table if not exists runs (
  run_id uuid primary key,
  call_type text not null check (call_type in ('kickoff', 'coaching')),
  status text not null check (status in ('pending', 'scoring', 'completed', 'failed')),
  transcript text not null,
  report jsonb,
  error_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists runs_created_at_idx on runs (created_at desc);
