# Design — api_fastapi

> How feature 7 is built. Decisions made before writing any code.

## Files created / modified

| File | Action | Purpose |
|---|---|---|
| `src/api/__init__.py` | create | package |
| `src/api/schemas.py` | create | HTTP request/response models |
| `src/api/dependencies.py` | create | DI providers (repo, llm, graph) |
| `src/api/routes.py` | create | `router` with the 3 endpoints |
| `src/api/app.py` | create | `create_app(repo, llm)` |
| `tests/test_api.py` | create | covers R2–R8 |

## Endpoints

```
POST /runs                  {transcript, call_type} -> 201 {run_id, url}
GET  /runs/{run_id}         -> RunResponse (status, report | error_reason)
GET  /runs/{run_id}/report.pdf -> application/pdf (attachment)
```

## Background scoring

`POST /runs` persists the run as `pending` and enqueues `FastAPI.BackgroundTasks`:
`pending -> scoring` (update) → `run_scoring()` → `completed` with a report or
`failed` with an `error_reason` (R8). The client may close the tab: the
result lives in the repository.

## New signatures

```python
# src/api/schemas.py
class CreateRunRequest(BaseModel): transcript: str; call_type: CallType
class CreateRunResponse(BaseModel): run_id: UUID; url: str
class RunResponse(BaseModel): run_id: UUID; call_type: CallType; status: RunStatus
                              report: Report | None; error_reason: str | None

# src/api/dependencies.py
def get_repo() -> RunRepository          # overridden in tests
def get_llm() -> GroqClient              # overridden in tests

# src/api/app.py
def create_app(repo: RunRepository, llm: GroqClient) -> FastAPI
```

## Decisions
- **FastAPI `BackgroundTasks`** instead of Celery/ARQ: the requirement is to
  survive the tab closing, not a process crash; state is persisted in the
  repository at every transition. An external worker is an operational
  dependency that the current scope does not justify.
- **App factory with explicit DI** (`create_app(repo, llm)`): tests use
  `InMemoryRunRepository` + `GroqClient(FakeTransport)` without global
  monkeypatching.
- **409 for the PDF of a run that is not completed** (R7): the resource exists
  but its representation does not yet; 404 stays reserved for nonexistent runs (R5).

## Alternative discarded
- Synchronous scoring inside the POST: discarded — an LLM call can take
  >30 s; the requirement "scoring survives the tab closing" implies an
  immediate response with a URL and decoupled processing.

## Traceability preview
- R1 → `test_app_factory_with_fakes`
- R2 → `test_post_run_creates_and_scores`
- R3 → `test_post_run_invalid_body`
- R4 → `test_get_run_completed_returns_report`, `test_get_run_failed_returns_reason`
- R5 → `test_get_run_not_found`
- R6 → `test_pdf_endpoint_returns_attachment`
- R7 → `test_pdf_endpoint_conflicts_when_not_completed`
- R8 → `test_background_outcome_persisted`
- R9 → code review + `test_error_messages_contain_no_secrets`
