# ADR — Architecture Decision Record

> This file is the **ADR template** that ships with the harness. When you start
> a new project on top of this repo, keep this file and use it to record every
> architectural and process decision of that project.
>
> It has two parts.
>
> **Part 1 (Baseline)** is defined by the developer when the project is created
> — it captures the structural decisions already made and locked in. Agents must
> treat these as fixed constraints, not open questions, and must not modify this
> part.
>
> **Part 2 (Decision Log)** is maintained by agents during execution: append an
> entry every time you make a decision, adopt an assumption, or face a trade-off
> that is not already covered in Part 1. Never delete or rewrite past entries —
> only append. If a new decision contradicts an earlier one, add a new entry
> that supersedes it and reference the entry it replaces.

---

## Part 1 — Baseline (set by developer, agents must not modify)

Fill this in when creating a new project. Entries marked **"inherited from
harness"** are defaults that every project built on the harness starts with;
change them only if the developer decides so.

### Project
- **Name:**
- **One-line description:**

### Core stack
- **Language(s):** Python 3.11+ (inherited from harness)
- **Framework(s):** Standard library by default; dependencies only when justified (inherited from harness)
- **Database / storage:**
- **Deployment target:**
- **Environment & deps:** `uv` (inherited from harness)
- **Tests:** `pytest` (inherited from harness)

### Structural decisions
Decisions already made and locked in — agents must treat these as fixed
constraints, not open questions.

| Decision | Rationale |
|---|---|
| Process and roles are documented model-agnostic in `docs/` and referenced from `AGENTS.md` | Works with Codex, Claude Code, and opencode without per-tool config |
| SDD (Spec Driven Development) is the canonical workflow | Human approval gate before any code; spec lives in `docs/specs.md` |
| `settings_files_tasks.json` is the single source of truth for features, rules, and statuses | Statuses and process stay auditable and machine-checkable |
| Features are tracked one at a time (`one_feature_at_a_time`) | Keeps sessions focused and reviews tractable |
| Specs and progress artifacts live in `specs/<feature>/` and `progress/` | Decisions and traceability persist to files, not chat |
| `uv run pytest` is the single verification gate | One command to prove a change is done |
| (add project-specific structural decisions here) | |

### Non-negotiables / constraints
- No new dependency without justification (name the alternative considered and why it lost).
- No code until the spec is human-approved (`require_approved_spec_to_implement`).
- No feature marked `done` with failing tests or missing coverage (`require_tests_to_close`).
- No secrets, keys, or credentials ever committed (see `.gitignore`).
- Agents must not modify Part 1 of this file.
- (add project-specific non-negotiables here)

---

## Part 2 — Decision Log (maintained by agents during execution)

> Append one entry per decision. Keep entries short and scannable. Use the
> template below for every new entry. A decision can be a technical choice, a
> process rule, an assumption, or a trade-off — if it matters to the why of the
> project, log it.

### Entry format
```
## [YYYY-MM-DD] Short decision title

**Decision:** What was decided.

**Reasoning:** Why this was decided — trade-offs considered, alternatives rejected.

**Source:** [User instruction | Agent assumption]
- If "Agent assumption," state explicitly what was assumed and flag it for developer review.

**Status:** [Active | Superseded by entry on YYYY-MM-DD]
```

### Log

## [2026-08-10] Skills live in skills/<name>/SKILL.md

**Decision:** Skills are stored model-agnostic in `skills/<name>/SKILL.md` and
referenced from `AGENTS.md` and `docs/`. Currently two skills ship with the
harness: `security-review` (used by the SDD reviewer review gate) and
`engineering-readme` (README authoring).

**Reasoning:** Keeps the harness tool-agnostic (Codex, Claude Code, opencode)
instead of duplicating skills into per-tool config directories. The `skills/`
folder follows the standard `<skill>/SKILL.md` convention so the files can be
copied into any tool-specific skill location without rewrite.

**Source:** [User instruction]

**Status:** [Active]

## [2026-08-23] Project repurposed: notes-cli → scoring-system

**Decision:** `settings_files_tasks.json` now tracks the scoring-system project
(operator pastes a transcript + call type, LangGraph agent scores it against
the kick-off/coaching rubric, report is served with a persistent per-run URL
and downloadable PDF). The 11 legacy notes-cli features were replaced by 10 new
features (backend-first; frontend last).

**Reasoning:** The repo's real goal is the scoring system (AGENTS.md, workflow
diagram, rubrics/, transcripts/, pdf_format.md). Keeping stale notes-cli
features would misroute the SDD flow. Legacy work is preserved in git history.

**Source:** [User instruction]

**Status:** [Active]

## [2026-08-23] Approved dependency set

**Decision:** Approved dependencies: `pydantic`, `langgraph`, `groq`-compatible
access via GPT-OSS 120B, `fpdf2`, `supabase`, `pytest` (fastapi already present).
Frontend dependency deferred until the UI technology is chosen.

**Reasoning:** All are declared in the AGENTS.md technical stack; each must
still earn its place per-feature in its spec's design.md.

**Source:** [User instruction]

**Status:** [Active]

## [2026-08-23] Frontend technology open: Streamlit vs React+Node

**Decision:** `frontend_dashboard` (feature 10) is specified
technology-agnostically. Candidates: Streamlit (as drawn in
workflow-beavermind.jpg) or React + Node.js. The decision will be made when
the backend features are done.

**Reasoning:** User stated the frontend is not well defined and wants to
finalize it after the backend. Note: React + Node implies a JS sub-project
outside the Python package; that trade-off will be recorded when decided.

**Source:** [User instruction]

**Status:** [Active]

## [2026-08-23] LLM accessed over stdlib HTTP instead of groq SDK

**Decision:** `llm_client` spec uses `urllib` with an injectable Transport to
call Groq (GPT-OSS 120B) rather than adding the `groq` SDK.

**Reasoning:** Only one endpoint is needed; the SDK would add a dependency and
duplicate exception handling. Recorded here because it deviates from the
literal stack list while respecting the "dependencies must earn their place"
rule.

**Source:** [Agent assumption] — flagged for developer review at spec approval.

**Status:** [Active]

<!-- Agent: append new entries below this line, most recent last -->
