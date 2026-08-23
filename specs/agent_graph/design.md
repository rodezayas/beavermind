# Design — agent_graph

> Cómo se construye la feature 4. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/agent/__init__.py` | create | paquete |
| `src/agent/state.py` | create | `ScoringState` (modelo tipado del estado) |
| `src/agent/sanitize.py` | create | `sanitize_transcript()` — anti prompt-injection |
| `src/agent/nodes.py` | create | `router_node`, `guardrail_node`, factories de scorer, helpers de ruta |
| `src/agent/graph.py` | create | `build_graph()`, `run_scoring()` |
| `tests/test_agent_graph.py` | create | cobertura R2–R12 |
| `pyproject.toml` | modify | agregar `langgraph` (aprobada) |

## New signatures

```python
# src/agent/state.py
class ScoringState(BaseModel):
    run_id: UUID
    call_type: CallType | None
    transcript: str          # ya sanitizado al salir de guardrails
    status: RunStatus
    report: Report | None = None
    error_reason: str | None = None
    current_node: str = "start"   # progreso, sobrevive al cierre de la pestaña
    sanitization_flags: list[str] = []  # R12: líneas de inyección removidas

# src/agent/sanitize.py
MAX_TRANSCRIPT_CHARS = 60_000
class SanitizationResult(BaseModel):
    text: str; flags: list[str]; too_long: bool
def sanitize_transcript(text: str) -> SanitizationResult

# src/agent/nodes.py  (todas puras: state in -> state out, R7)
def router_node(state: ScoringState) -> ScoringState
def guardrail_node(state: ScoringState) -> ScoringState   # R5, R10–R12
def make_score_node(call_type: CallType, scoring_fn: ScoringFn) -> NodeFn
def route_after_router(state) -> str   # "guardrails" | END
def route_after_guardrails(state) -> str  # nombre del scorer | END

# src/agent/graph.py
ScoringFn = Callable[[CallType, str], Report]  # inyectable; feature 5 lo provee
def build_graph(scoring_fn: ScoringFn) -> CompiledGraph   # R9
def run_scoring(run: Run, scoring_fn: ScoringFn) -> ScoringState
```

## Graph topology

```
START -> router -> guardrails -> (score_kickoff | score_coaching) -> END
                     |                        |
                     +-------> END <----------+  (estado failed en el state)
```

- Arista condicional 1 (router): `guardrails` o `END` según validez de
  `call_type` (R3, R4).
- Arista condicional 2 (guardrails): al scorer correspondiente o `END`
  con estado failed (R5, R11).
- El error boundary vive dentro de `make_score_node` (try/except → failed,
  R6): LangGraph nunca ve una excepción salir de un nodo.

## Decisions
- **`scoring_fn` inyectada en `build_graph`** (tipo `ScoringFn`): el grafo no
  depende de la implementación de scoring (feature 5); los tests inyectan un
  fake y la API (feature 7) conecta `src.scoring`. Mismo patrón DI que
  `GroqClient`.
- **LangGraph StateGraph con modelo Pydantic como state_schema**: el estado
  tipado (R2) viaja entre nodos y es serializable para persistir progreso.
- **Guardrail antes del scorer** (R5): evita gastar tokens LLM en transcripts
  inservibles; el mínimo de 4 turns `[Speaker]:` evita falsos positivos.
- **Sanitización determinista, no por LLM** (R10–R12): regex + limpieza de
  caracteres; un sanitizador basado en otro LLM sería circular y no auditable.
- **`current_node` + `sanitization_flags` en el estado**: progreso y
  auditoría mínimos, persistibles por la capa de base de datos.

## Alternative discarded
- Un solo nodo monolítico con `if call_type == ...`: descartado porque mezcla
  router, guardrails y scoring en una función no testeable por separado
  (viola R7 y la regla "one concern per file" de AGENTS.md).

## Traceability preview
- R3 → `test_router_routes_to_kickoff_branch` / `..._coaching_branch`
- R4 → `test_router_fails_on_missing_call_type`
- R5 → `test_guardrail_rejects_empty_transcript`, `test_guardrail_rejects_short_transcript`
- R6 → `test_scorer_exception_marks_run_failed`
- R7 → los tests invocan nodos individualmente
- R8 → `test_completed_scoring_sets_report_and_status`
- R10 → `test_sanitize_strips_control_and_zero_width_chars`
- R11 → `test_guardrail_rejects_oversized_transcript`
- R12 → `test_injection_lines_removed_and_flagged`
- R13 → verificado en el spec de `scoring_report` (R8); revisión cruzada al implementarla
