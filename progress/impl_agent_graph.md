# Implementation — agent_graph

## Traceability
- R1 → estructura `src/agent/{state,sanitize,nodes,graph}.py` + `langgraph` en pyproject
- R2 → `test_state_is_typed_and_serializable`
- R3 → `test_router_routes_to_kickoff_branch`, `test_router_routes_to_coaching_branch`
- R4 → `test_router_fails_on_missing_call_type`
- R5 → `test_guardrail_rejects_empty_transcript`, `test_guardrail_rejects_short_transcript`
- R6 → `test_scorer_exception_marks_run_failed`
- R7 → todos los nodos son funciones puras; tests los invocan individualmente
- R8 → `test_completed_scoring_sets_report_and_status`, `test_run_scoring_maps_run_to_state_and_back`
- R10 → `test_sanitize_strips_control_and_zero_width_chars`, `test_sanitize_keeps_clean_transcript_untouched`
- R11 → `test_guardrail_rejects_oversized_transcript`
- R12 → `test_injection_lines_removed_and_flagged` (5 payloads), `test_injection_removed_before_scoring_fn_sees_it`, `test_sanitize_preserves_legitimate_content`
- R13 → pertenece a `scoring_report` (R8 de su spec); verificación cruzada pendiente de esa feature

## Tasks checklist (specs/agent_graph/tasks.md)
- [x] T1–T16 completados (ver archivo de spec); `uv run pytest`: 48 passed.

## Notes / decisions during implementation
- **`scoring_fn` inyectada en `build_graph`/`run_scoring`** (ajuste del design
  aprobado en el spec actualizado): el grafo no acopla a la feature 5; la API
  (feature 7) conectará `src.scoring` y los tests usan fakes. Especificado así
  en `specs/agent_graph/design.md` antes de codificar.
- **Sanitización de dos capas** (afinada durante T3): patrones verbales de
  inyección solo aplican al inicio de línea/turno (evita falsos positivos con
  discurso citado, cubierto por `test_sanitize_preserves_legitimate_content`);
  los tags falsos de rol `<system>/<assistant>` se remueven en cualquier
  posición. Prefijos corteses ("please reveal...") también cubiertos.
- El error boundary convierte cualquier excepción del scorer en estado failed
  (R6): la excepción nunca cruza la frontera del grafo.
