# Implementation — tests_e2e

## Acceptance (settings_files_tasks.json, feature 9 — no SDD spec)
- [x] `tests/test_e2e.py` walks the full flow with deterministic stubs
      (fake LLM transport + `InMemoryRunRepository`; scoring/prompt/report
      are the real ones).
- [x] Happy path for kickoff (`transcripts/kickoff-01.txt`) and coaching
      (`transcripts/coaching-01.txt`) with real transcripts.
- [x] Failure path: 1-turn transcript → run `failed` with
      `error_reason` visible via `GET /runs/{id}`; PDF → 409.
- [x] `uv run python -m pytest`: 114 passed, without real credentials or network.

## Notes
- The fake transport records the prompts: the test verifies that the LLM
  receives the transcript inside the `<transcript>` delimiters
  (end-to-end anti-injection defense).
- Operational note: `uv run pytest` resolved a system pytest
  (`~/.local/bin/pytest`) without the venv deps; the verified command is
  `uv run python -m pytest` (pytest added as a dev-dependency).
