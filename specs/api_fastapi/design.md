# Design — api_fastapi

> Cómo se construye la feature 7. Decisiones tomadas antes de escribir código.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/api/__init__.py` | create | paquete |
| `src/api/schemas.py` | create | request/response models HTTP |
| `src/api/dependencies.py` | create | proveedores DI (repo, llm, graph) |
| `src/api/routes.py` | create | `router` con los 3 endpoints |
| `src/api/app.py` | create | `create_app(repo, llm)` |
| `tests/test_api.py` | create | cobertura R2–R8 |

## Endpoints

```
POST /runs                  {transcript, call_type} -> 201 {run_id, url}
GET  /runs/{run_id}         -> RunResponse (status, report | error_reason)
GET  /runs/{run_id}/report.pdf -> application/pdf (attachment)
```

## Background scoring

`POST /runs` persiste el run `pending` y encola `FastAPI.BackgroundTasks`:
`pending -> scoring` (update) → `run_scoring()` → `completed` con reporte o
`failed` con `error_reason` (R8). El cliente puede cerrar la pestaña: el
resultado vive en el repository.

## New signatures

```python
# src/api/schemas.py
class CreateRunRequest(BaseModel): transcript: str; call_type: CallType
class CreateRunResponse(BaseModel): run_id: UUID; url: str
class RunResponse(BaseModel): run_id: UUID; call_type: CallType; status: RunStatus
                              report: Report | None; error_reason: str | None

# src/api/dependencies.py
def get_repo() -> RunRepository          # override en tests
def get_llm() -> GroqClient              # override en tests

# src/api/app.py
def create_app(repo: RunRepository, llm: GroqClient) -> FastAPI
```

## Decisions
- **`BackgroundTasks` de FastAPI** en vez de Celery/ARQ: el requisito es
  sobrevivir al cierre de la pestaña, no a la caída del proceso; el estado se
  persiste en el repository en cada transición. Un worker externo es una
  dependencia operativa que el alcance actual no justifica.
- **App factory con DI explícita** (`create_app(repo, llm)`): los tests usan
  `InMemoryRunRepository` + `GroqClient(FakeTransport)` sin monkeypatching
  global.
- **409 para PDF de run no completado** (R7): el recurso existe pero su
  representación aún no; 404 quedaría reservado a runs inexistentes (R5).

## Alternative discarded
- Scoring síncrono dentro del POST: descartado — una llamada LLM puede tardar
  >30 s; el requisito "el scoring sobrevive al cierre de la pestaña" implica
  respuesta inmediata con URL y procesamiento desacoplado.

## Traceability preview
- R1 → `test_app_factory_with_fakes`
- R2 → `test_post_run_creates_and_scores`
- R3 → `test_post_run_invalid_body`
- R4 → `test_get_run_completed_returns_report`, `test_get_run_failed_returns_reason`
- R5 → `test_get_run_not_found`
- R6 → `test_pdf_endpoint_returns_attachment`
- R7 → `test_pdf_endpoint_conflicts_when_not_completed`
- R8 → `test_background_outcome_persisted`
- R9 → revisión de código + `test_error_messages_contain_no_secrets`
