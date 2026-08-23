# Project Context
Scoring System that emulates an operator. The operator pastes a call transcript, says whether it is a kick-off or a coaching call, and the system scores it against that rubric and returns a report they can download as a PDF.
Every run gets its own URL that still works next week, the scoring survives the tab closing, and a failed run says why.
## Business Tasks
- Transcripts/mock data: transcripts
- PDF rules in: /home/rodezayas/dev-challenge/pdf_format.md
- Workflow: workflow-beavermind.jpg
## Code Standards
- Use Python 3.11+
- Document classes and functions with docstrings and variables with comments to make their purpose clear
- Separate responsibilities: one file per concern. E.g.: (state, nodes, graph, schemas)

## Conventions
- Naming: `snake_case` for files, modules and functions; `UpperCamelCase` for classes; constants in `SCREAMING_SNAKE_CASE`
- Type hints are mandatory on function and method signatures
- Every public class and function has a docstring; add comments to non-obvious variables
- Error handling is explicit: clear error messages, never swallow exceptions with a bare `except:`, use `raise` with context
- Tests are mandatory: any new logic ships with its test; run `uv run pytest` before considering a change done
- One concern per file (do not mix unrelated responsibilities in a single module)

## Dependencies
- Always use uv packages
- Do not add new dependencies without asking first
- Default to the standard library or a small vendored snippet
- Every package added to pyproject.toml should earn its place
- When proposing a new dependency, name the alternative you considered and why it lost

## Project Structure - Example
- `src/` — Application code (one package per project)
- `tests/` — Project tests
- `docs/` — ADRs and specs (SDD)
- `specs/<feature>/` — requirements/design/tasks per feature
- `progress/` — Implementation and review reports
- `scripts/` — Setup and verification helpers

## Skills
- `skills/security-review/SKILL.md` — security review of application code and architecture. Use in any review gate (e.g. the SDD reviewer).
- `skills/engineering-readme/SKILL.md` — write or update project READMEs.

## Tecnical Stack
- Python 3.11+
- uv for environment and dependencies
- pytest for tests
- Prefer the standard library; only add dependencies when justified
- FastAPI, LangGraph, Pydantic, fpdf2, Supabase, Groq(OpenAI GPT-OSS 120B)

## Workflow (Spec Driven Development)
- Follow `docs/specs.md` (canonical process and agent roles: leader, spec_author, implementer, reviewer)
- Features and their states live in `settings_files_tasks.json`
- One feature at a time; no code until the spec is human-approved
- Run `uv run pytest` before considering a change done
