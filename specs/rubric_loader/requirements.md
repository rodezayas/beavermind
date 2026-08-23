# Requirements — rubric_loader

> Feature 2 de `settings_files_tasks.json`. Estado: `spec_ready` (esperando aprobación humana).

## R1
The system MUST expose `load_rubric(call_type: CallType) -> Rubric` in
`src/rubrics.py` that parses the matching markdown file under `rubrics/`
(`coaching-call-rubric.md` for coaching, `kickotff-call-rubric.md` for kickoff).

## R2
`Rubric` MUST expose exactly 12 dimensions, each with `id`, `name` and
`max_points`.

## R3
The dimension `max_points` values MUST sum to 100 for both rubrics.

## R4
`Rubric` MUST expose the score bands using exactly the names `Elite`,
`Strong`, `Inconsistent`, `At risk`, `Fail` as defined by the rubrics.

## R5
`Rubric` MUST expose the "Global Automatic Score Caps" declared in each
rubric markdown (cap rule → affected dimension → max score).

## R6
The coaching rubric MUST mark Dimension 4 (Movement Coaching Quality) as
optional; `Rubric.max_possible` MUST return 85 when that dimension is
disabled and 100 otherwise.

## R7
IF `load_rubric` receives a `call_type` without a matching rubric file THEN
the system MUST raise an exception whose message names the call type and the
missing path.

## R8
IF the rubric markdown cannot be parsed into the expected structure (missing
dimension headers or point values) THEN the system MUST raise a parse error
identifying the offending line, never return a partially built `Rubric`.
