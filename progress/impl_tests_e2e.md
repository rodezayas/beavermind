# Implementation — tests_e2e

## Acceptance (settings_files_tasks.json, feature 9 — sin spec SDD)
- [x] `tests/test_e2e.py` recorre el flujo completo con stubs deterministas
      (transporte LLM falso + `InMemoryRunRepository`; el scoring/prompt/report
      son los reales).
- [x] Camino feliz para kickoff (`transcripts/kickoff-01.txt`) y coaching
      (`transcripts/coaching-01.txt`) con transcripts reales.
- [x] Camino de fallo: transcript de 1 turno → run `failed` con
      `error_reason` visible vía `GET /runs/{id}`; PDF → 409.
- [x] `uv run python -m pytest`: 114 passed, sin credenciales reales ni red.

## Notes
- El transporte falso registra los prompts: el test verifica que el LLM
  recibe el transcript dentro de los delimitadores `<transcript>`
  (defensa anti-inyección de punta a punta).
- Nota operativa: `uv run pytest` resolvía un pytest del sistema
  (`~/.local/bin/pytest`) sin las deps del venv; el comando verificado es
  `uv run python -m pytest` (pytest añadido como dev-dependency).
