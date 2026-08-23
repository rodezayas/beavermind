# Design — agent_graph

> Cómo se construye la feature 4. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/agent/__init__.py` | create | paquete |
| `src/agent/state.py` | create | `ScoringState` (modelo tipado del estado) |
| `src/agent/nodes.py` | create | `router_node`, `guardrail_node`, `score_kickoff_node`, `score_coaching_node`, `error_boundary` |
| `src/agent/graph.py` | create | `build_graph()`, `run_scoring()` |
| `tests/test_agent_graph.py` | create | cobertura R2–R7 |
| `pyproject.toml` | modify | agregar `langgraph` (aprobada) |

## New signatures

```python
# src/agent/state.py
class ScoringState(BaseModel):
    run_id: UUID
    call_type: CallType | None
    transcript: str
    status: RunStatus
    report: Report | None = None
    error_reason: str | None = None
    current_node: str = "start"   # progreso, sobrevive al cierre de la pestaña

# src/agent/nodes.py  (todas puras: state in -> state out, R7)
def router_node(state: ScoringState) -> ScoringState
def guardrail_node(state: ScoringState) -> ScoringState   # R5
def score_kickoff_node(state: ScoringState, llm: GroqClient) -> ScoringState
def score_coaching_node(state: ScoringState, llm: GroqClient) -> ScoringState
def fail(state, reason: str) -> ScoringState              # helper R4/R5/R6

# src/agent/graph.py
def build_graph(llm: GroqClient) -> CompiledGraph   # R9
def run_scoring(run: Run, llm: GroqClient) -> ScoringState
```

## Graph topology

```
START -> router -> guardrails -> (kickoff | coaching) -> END
                     |                  |
                     +--> failed -> END <-+  (cualquier nodo puede fallar, R6)
```

- Arista condicional 1 (router): `kickoff | coaching | failed` según `call_type` (R3, R4).
- Arista condicional 2 (tras scoring): `completed | failed` (R6, R8).
- `run_scoring` envuelve la invocación y mapea `ScoringState` ↔ `Run`.

## Decisions
- **LangGraph StateGraph con modelo Pydantic como state_schema**: el estado
  tipado (R2) viaja entre nodos y es serializable para persistir progreso.
- **LLM inyectado por closure en `build_graph(llm)`**, no global: los tests
  pasan un `GroqClient` con `FakeTransport` (sin red).
- **Guardrail antes del scorer** (R5): evita gastar tokens LLM en transcripts
  inservibles; el mínimo de 4 turns `[Speaker]:` evita falsos positivos con
  transcripciones de una línea.
- **`current_node` en el estado**: marca de progreso mínima para que la capa
  de base de datos pueda persistir dónde quedó el run.

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
