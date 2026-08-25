# Requirements — project_scaffold

> Feature 1 of `settings_files_tasks.json`. Status: `spec_ready` (awaiting human approval).

## R1
The system MUST expose a `Settings` object in `src/config.py` that reads
`SUPABASE_PROJECT_ID`, `SUPABASE_API_KEY`, `SUPABASE_SECRET_KEY`,
`GROQ_API_KEY` and `DATABASE` from the environment (`.env`).

## R2
IF a mandatory environment variable is missing or empty THEN the system MUST
raise a configuration error whose message names the missing variable.

## R3
The system MUST define `CallType` with exactly the values `kickoff` and
`coaching`.

## R4
The system MUST define a `Run` model with fields `run_id` (UUID), `call_type`,
`status`, `transcript`, `report` (optional), `error_reason` (optional) and
`created_at` / `updated_at` (ISO 8601).

## R5
The `Run` model MUST support exactly the statuses `pending`, `scoring`,
`completed`, `failed`.

## R6
IF a `Run` has status `failed` THEN the model MUST reject it when
`error_reason` is absent or empty.

## R7
The system MUST define a `DimensionScore` model with `dimension_id`, `name`,
`score` (optional, `None` when disabled), `max_points`, `band` (optional),
`reasoning`, `transcript_lines`, `quick_fix`, `disabled` and `disabled_reason`.

## R8
WHEN a dimension is disabled (`disabled: true`) THEN the model MUST accept
`score: None` and `band: None` and MUST require a non-empty `disabled_reason`.

## R9
The system MUST define a `Report` model containing `one_thing` (including the
hypothetical score the call would reach if applied), `brief`, `red_flags`,
`grade` (total + band) and a list of exactly 12 `DimensionScore` entries.
