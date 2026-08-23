# Spec Driven Development (SDD)

> This project follows a Kiro-style flow: requirements → design → tasks → code.
> No code is written until a spec is approved by a human.

`docs/specs.md` is the **canonical source of truth** for the SDD process and
the agent roles in this harness. It is model-agnostic: it works with Codex,
Claude Code, or opencode. Every tool reads `AGENTS.md` as global context, and
`AGENTS.md` points here for the workflow.

## Structure

Every new feature (`"sdd": true` in `settings_files_tasks.json`) gets a
dedicated folder as soon as it leaves `pending`:

```
specs/<feature-name>/
├── requirements.md   # WHAT is needed (EARS notation)
├── design.md          # HOW it will be built (technical decisions)
└── tasks.md           # CONCRETE steps to implement
```

The `feature-name` matches the `name` field in `settings_files_tasks.json`.

## Feature states

| Status       | Meaning                                                                  |
|--------------|--------------------------------------------------------------------------|
| `pending`    | No spec yet. The `spec_author` is the first to act.                      |
| `spec_ready` | Spec drafted. Awaiting human approval. NO code is touched.               |
| `in_progress`| Spec approved. `implementer` working.                                    |
| `done`       | Code green, `reviewer` approved, session closed.                         |
| `blocked`    | Stuck. Reason in `progress/current.md`.                                  |

These match the `valid_status` list in the `rules` of
`settings_files_tasks.json`.

## The human approval gate

The automated flow stops **once**: when the `spec_author` finishes its three
files it marks the feature as `spec_ready` and stops. A human reads
`specs/<feature>/` and says "approved" (or requests changes).

Only then the `leader` transitions `spec_ready → in_progress` and launches the
`implementer`.

```
pending → [spec_author] → spec_ready → ⏸ HUMAN → in_progress → [implementer → reviewer] → done
```

This maps to the rule `require_approved_spec_to_implement` in
`settings_files_tasks.json`.

## Rules (mapped to settings_files_tasks.json)

The SDD flow is configured by the `rules` in `settings_files_tasks.json`; keep
this doc and that file consistent.

| Rule                            | Effect                                                                      |
|----------------------------------|-----------------------------------------------------------------------------|
| `one_feature_at_a_time`         | Only one feature is worked on per session (a single feature in `in_progress`). |
| `require_tests_to_close`         | A feature cannot be marked `done` while any `R<n>` lacks a test.            |
| `require_approved_spec_to_implement` | Maps to the human approval gate between `spec_ready` and `in_progress`. |
| `sdd_required_when`              | SDD applies to features with `"sdd": true`.                                 |
| `valid_status`                   | The only allowed statuses (`pending`, `spec_ready`, `in_progress`, `done`, `blocked`). |

## Roles

The SDD process relies on four roles. They are defined here independently of
any specific tool; each tool maps them to its own agent mechanism (a primary
agent that follows these instructions, or subagents where supported).

### Leader (orchestrator)

- Breaks the top-level task into work and coordinates, never implements.
- Reads `AGENTS.md`, `docs/specs.md`, `settings_files_tasks.json`, and
  `docs/ADR.md` before starting.
- Picks the first feature that is not `done` / not `blocked` and routes it
  through the SDD flow.
- Enforces `one_feature_at_a_time` and the human approval gate.
- **Does NOT** edit code, mark features `done`, or skip the human gate.

### spec_author

- Writes `specs/<name>/{requirements.md, design.md, tasks.md}`
  for the feature and sets its status to `spec_ready`.
- Only the three spec files, then stops for human approval.
- requirements use strict EARS; design.md captures decisions before code.

### implementer

- Implements exactly **one** feature from an **approved** spec; never from raw
  `acceptance`.
- Reads `AGENTS.md`, `docs/ADR.md` (baseline + decision log), and the full
  `specs/<name>/` folder before touching code.
- For each task in `tasks.md`: implements it, writes its test, checks it off.
- Verifies the suite is green (`uv run pytest`) before finishing.
- Documents the `R<n> → test` traceability map in `progress/impl_<name>.md`.
- Does **not** mark the feature `done`; that is the reviewer's call.
- If a task cannot be done without deviating from the spec, stops and asks for
  spec changes instead of inventing requirements.

### reviewer

- Strictly approves or rejects the implementer's work; never edits code.
- Verifies: every `R<n>` has at least one concrete test; all tasks in
  `tasks.md` are checked off; code respects `docs/ADR.md` and `AGENTS.md`
  conventions; `uv run pytest` is green.
- Runs the security review defined in `skills/security-review/SKILL.md`
  before approving.
- Writes the verdict (`APPROVED` or `CHANGES_REQUESTED`) to
  `progress/review_<name>.md`.
- Rejects if tests are red, a requirement lacks coverage, or tasks remain
  incomplete without a documented justification.

Anti-telephone rule (shared): agents write their results to files
(`specs/<name>/`, `progress/*`) and only report a reference to the file, not
dump the full content in the message channel.

## requirements.md — strict EARS

Requirements are written in **EARS** (Easy Approach to Requirements Syntax).
Each requirement is a numbered paragraph using one of five patterns:

| Pattern        | Template                                                      |
|----------------|---------------------------------------------------------------|
| **Ubiquitous** | `The system must <action>.`                                   |
| **Event**      | `WHEN <trigger>, the system must <action>.`                   |
| **State**      | `WHILE <state>, the system must <action>.`                    |
| **Optional**   | `WHERE <optional feature>, the system must <action>.`         |
| **Unwanted**   | `IF <unwanted event> THEN the system must <action>.`          |

Hard rules:

- Each requirement has a stable id: `R1`, `R2`, ...
- Each requirement must be verifiable by at least one concrete test.
- Do not mix multiple `MUST` clauses in a single requirement; split them.
- Do not use weak verbs ("could", "might", "supports"). Use `MUST` / `MUST NOT`.

Example:

```markdown
## R1
When the user runs the `list` command, the system MUST print one line per note.

## R2
IF `--limit` is a value <= 0 THEN the system MUST print an error to
stderr and exit with a non-zero code.
```

## design.md — technical decisions

Be written **before** touching code:

- What files are created / modified.
- What new signatures appear (functions, classes, commands).
- What exceptions are reused or added.
- What alternative was discarded and why (at least one).

Base the design on `docs/ADR.md` (Part 1 baseline sets hard constraints, Part 2
decision log records trade-offs) and `AGENTS.md` conventions. Each decision
recorded here should also be appended to the decision log in
`docs/ADR.md`.

## tasks.md — executable checklist

Discrete steps in order, each with a checkbox. Each task references at least
one `R<n>` it covers.

Example:

```markdown
- [ ] T1 — Add the `list` command. Covers: R1, R3.
- [ ] T2 — Register the `list` subcommand. Covers: R1, R2.
- [ ] T3 — Add `test_list_default` in the tests. Covers: R1.
- [ ] T4 — Add `test_list_invalid_limit` in the tests. Covers: R2.
```

The implementer checks `[x]` off each task when done. The reviewer rejects if
any task stays `[ ]` without a justified reason documented in
`progress/impl_<name>.md`.

## Traceability (hard rule)

- Every test must map back to an `R<n>` of its spec.
- Every `R<n>` must have at least one concrete test.
- The reviewer explicitly checks this correspondence and rejects if missing.

The implementer documents the mapping in `progress/impl_<name>.md`:

```markdown
## Traceability
- R1 → `test_list_default`
- R2 → `test_list_invalid_limit`
- R3 → `test_list_custom_limit`
```

## When SDD does NOT apply

Features with `"sdd": false` or without the `sdd` field (the legacy features,
e.g. ids 1–6 in the current payload) have no spec. SDD only applies forward.