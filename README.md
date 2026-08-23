repo: https://github.com/lukecala/hiring-ai-dev-exercise

# Scoring System

Emulador de operador: se pega un transcript de llamada, se indica si es
*kick-off* o *coaching*, y el sistema lo puntúa contra la rúbrica
correspondiente (12 dimensiones) y genera un reporte descargable como PDF.
Cada run obtiene una URL propia persistente; un run fallido reporta por qué
falló.

## Nota sobre las rúbricas (ajuste documentado)

La rúbrica original de coaching (`rubrics/coaching-call-rubric.md`) declaraba
"Twelve dimensions, 100 points" y "Total is 100 points when D4 is active, 85
when switched off", pero la suma real de sus dimensiones era **105**
(D6 — Action Steps & Accountability valía 15 pts en lugar de 10).

**Ajuste aplicado:** se redujo D6 de 15 → 10 pts (buckets 10/7/3/0 y cap
"Max 7/10 on D6") para que la suma sea exactamente 100 con D4 activa y 85
con D4 deshabilitada, tal como la propia rúbrica declara. La rúbrica de
kick-off no requería cambios (sumaba 100 exacto).

## Desarrollo

- Stack: Python 3.11+, uv, pytest, FastAPI, LangGraph, Pydantic, fpdf2, Supabase, Groq (GPT-OSS 120B).
- Workflow: Spec Driven Development — ver `docs/specs.md`. Features y estados en `settings_files_tasks.json`.
- Verificación: `uv run pytest`.
