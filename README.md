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

## Problemas encontrados en la verificación real (feature 11) y sus soluciones

Durante el E2E con credenciales reales (Supabase + Groq) aparecieron tres
problemas, ya resueltos en el código:

1. **Cloudflare bloqueaba las llamadas a Groq (HTTP 403, error 1010).**
   El cliente HTTP usa `urllib`, cuyo User-Agent por defecto
   (`Python-urllib/3.x`) está bloqueado por Cloudflare delante de la API de
   Groq. Solución: cabecera `User-Agent: scoring-system/1.0` explícita en
   `src/llm_client.py`.

2. **El prompt excedía el límite de tokens del free tier (HTTP 413).** Groq
   free tier permite 8000 TPM; los transcripts reales (~34k chars ≈ 8.6k
   tokens) más la rúbrica superaban el límite. Solución: presupuesto
   `PROMPT_TRANSCRIPT_BUDGET_CHARS = 16_000` en `src/scoring.py`; los
   transcripts más largos se truncan conservando el inicio de la llamada y
   marcando el corte (`[... transcript truncated for length ...]`). Si se
   necesita puntuar llamadas completas sin recorte, hay que subir de tier en
   Groq.

3. **La tabla real de Supabase difiere del schema original.** La tabla del
   proyecto se llama `beaverops` (no `runs`) y su columna de timestamp es
   `updatet_at` (typo incluido, `timestamp without time zone`). El repositorio
   (`src/database/repository.py`) usa esas constantes y mapea
   `updatet_at` ↔ `updated_at` para que el modelo de dominio no cambie.
   `src/database/schema.sql` refleja la tabla tal como existe.

Además, se eliminó `exclude-newer = "7 days"` de `[tool.uv]` en
`pyproject.toml`: uv no interpreta ese valor como fecha relativa y rompía el
parseo de settings en cada ejecución.

## Decisión: sin límite de longitud de transcript

El guardrail original fallaba el run cuando el transcript superaba
`MAX_TRANSCRIPT_CHARS` (60k chars). En la práctica los transcripts reales
(~64k chars) disparaban ese fallo, así que se cambió el comportamiento:

- **Cualquier longitud se acepta.** La sanitización anti-inyección se
  mantiene (protege la integridad del scoring; no limita tamaño).
- El prompt se trunca al presupuesto `PROMPT_TRANSCRIPT_BUDGET_CHARS`
  (16k chars) para respetar el rate limit del free tier de Groq (8000 TPM).
  El modelo no es el cuello de botella: GPT-OSS-120B acepta 131k de
  contexto; el límite es de tarifa, no de capacidad.
- Trade-off conocido: en llamadas muy largas el scoring se basa en el inicio
  del transcript. Para cobertura completa hay dos caminos: subir a Groq Dev
  Tier (más TPM, sin cambios de código) o implementar scoring por chunks
  multi-pasada.

## Desarrollo

- Stack: Python 3.11+, uv, pytest, FastAPI, LangGraph, Pydantic, fpdf2, Supabase, Groq (GPT-OSS 120B).
- Workflow: Spec Driven Development — ver `docs/specs.md`. Features y estados en `settings_files_tasks.json`.
- Verificación: `uv run pytest`.
