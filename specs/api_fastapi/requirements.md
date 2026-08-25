# Requirements — api_fastapi

> Feature 7 of `settings_files_tasks.json`. Status: `spec_ready` (awaiting human approval).

## R1
The system MUST expose a FastAPI application factory `create_app(repo,
llm) -> FastAPI` in `src/api/app.py` with routes defined in
`src/api/routes.py`, receiving the repository and LLM client by dependency
injection.

## R2
WHEN `POST /runs` receives a valid body (`transcript` non-empty,
`call_type` in {kickoff, coaching}) THEN the API MUST respond `201` with
`run_id` and the run URL (`/runs/{run_id}`), persist the run in state
`pending`, and start the scoring in the background.

## R3
IF `POST /runs` receives an empty transcript or an unknown `call_type` THEN
the API MUST respond `422` with a message naming the invalid field.

## R4
WHEN `GET /runs/{run_id}` is called for an existing run THEN the API MUST
return its `status`; and additionally the `report` when `completed`, or the
`error_reason` when `failed`.

## R5
IF `GET /runs/{run_id}` receives an id that does not exist THEN the API MUST
respond `404` with a clear message.

## R6
WHEN `GET /runs/{run_id}/report.pdf` is called for a `completed` run THEN the
API MUST return the rendered PDF as
`application/pdf` with `Content-Disposition: attachment`.

## R7
IF `GET /runs/{run_id}/report.pdf` is called for a run that is not
`completed` THEN the API MUST respond `409` explaining that the report is not
ready (or the run failed, including its reason).

## R8
WHEN the background scoring finishes or fails THEN the API layer MUST persist
the outcome through the repository, so the result survives the HTTP request
and the client tab closing.

## R9
The API MUST NOT expose any secret (API keys, service credentials) in
responses or error messages.
