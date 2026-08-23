# Requirements — frontend_dashboard

> Feature 10 de `settings_files_tasks.json`. Estado: `spec_ready` (esperando aprobación humana).
> **Nota:** la tecnología de UI está abierta (Streamlit vs React + Node.js); estos requisitos
> son tecnológicamente neutrales. La decisión se registra en `design.md` y se cierra antes
> de implementar.

## R1
The UI MUST let the operator paste a call transcript and select the call type
(kick-off | coaching) before submitting.

## R2
WHEN the operator submits a transcript THEN the UI MUST call `POST /runs`,
display the unique run URL, and show the live run status
(pending / scoring / completed / failed).

## R3
WHEN the run is `completed` THEN the UI MUST render the report: the one
thing, the brief, the red flags, the grade (total + band), and the 12
dimensions each showing score over maximum, reasoning, transcript evidence
and quick fix.

## R4
WHEN the run is `failed` THEN the UI MUST display the failure reason
prominently (not a generic error).

## R5
WHEN the run is `completed` THEN the UI MUST offer a button that downloads
the run's PDF (`GET /runs/{id}/report.pdf`).

## R6
WHEN a run URL is opened later (new session, days after) THEN the UI MUST
render the stored outcome from `GET /runs/{run_id}` without re-running the
scoring.

## R7
The UI MUST communicate API failures with the reason returned by the API,
never a silent failure.

## R8
The UI client logic (functions that call the API and map responses/errors to
view state) MUST live in Python-callable, testable modules covered by tests.
