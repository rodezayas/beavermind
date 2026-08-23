# Design — frontend_dashboard

> Cómo se construye la feature 10. **La tecnología está abierta**: este design
> deja registradas ambas opciones y el criterio de decisión. Se cierra antes
> de implementar (decisión del humano).

## Opción A — Streamlit (workflow-beavermind.jpg)

| Aspecto | Evaluación |
|---|---|
| Esfuerzo | Mínimo: una página, `st.text_area`, `st.selectbox`, polling con `st.rerun` |
| Riesgo | Bajo: todo Python, reusa `src/` directamente |
| Contras | Menos control visual fino; polling menos elegante |

## Opción B — React + Node.js

| Aspecto | Evaluación |
|---|---|
| Esfuerzo | Alto: sub-proyecto JS (build, tooling, CORS), duplica tipos |
| Riesgo | Medio: nueva cadena de herramientas fuera del repo Python |
| Contras | AGENTS.md es Python-first; cada tipo del reporte se duplica en TS |

## Criterio de decisión (para el humano)
- Si el dashboard es interno para el operador → **A (Streamlit)**: cumple R1–R7
  con una fracción del esfuerzo y cero dependencias nuevas fuera del stack.
- Si el dashboard es producto visible para clientes con identidad visual
  propia → **B (React)**: el coste extra compra control total del look.

## Estructura común (independiente de la elección)

| File | Purpose |
|---|---|
| `src/frontend/api_client.py` | `ScoringApiClient`: `create_run()`, `get_run()`, `download_pdf()`; mapea errores HTTP a `ApiClientError(reason)` |
| `src/frontend/app.<ext>` | la vista: formulario, estado del run, reporte, botón PDF |
| `tests/test_frontend_client.py` | cobertura R2–R7 contra un `FakeApi` (httpx MockTransport o stub propio) |

## Decisions
- **El cliente de API vive en Python testeable** (`src/frontend/api_client.py`,
  R8) pase lo que pase con la vista: la lógica de llamadas y manejo de errores
  es lo testeable; el render es del framework.
- **Polling del estado** mientras `pending`/`scoring` (R2): intervalo fijo de
  ~2 s hasta `completed`/`failed`.
- **La decisión de tecnología se registra en `docs/ADR.md`** antes de
  implementar (gate adicional dentro de esta feature).

## Alternative discarded
- Servir el dashboard desde FastAPI con Jinja2 + HTMX: descartada por ahora —
  mezcla responsabilidades del API (feature 7 ya cerrada como JSON API) con la
  vista; se reconsiderará si el humano elige un punto medio.

## Traceability preview
- R1 → `test_create_run_sends_transcript_and_call_type`
- R2 → `test_run_url_and_status_shown`
- R3 → `test_completed_report_mapped_to_view`
- R4 → `test_failed_reason_surfaced`
- R5 → `test_pdf_download_url`
- R6 → `test_get_run_without_rescoring`
- R7 → `test_api_error_reason_propagated`
