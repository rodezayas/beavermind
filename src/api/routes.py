"""API routes: create runs, consult them, download the PDF report."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response

from src.agent.graph import run_scoring
from src.agent.nodes import ScoringFn
from src.api.dependencies import get_llm, get_repo, get_scoring_fn
from src.api.schemas import CreateRunRequest, CreateRunResponse, RunResponse
from src.database.repository import RunRepository
from src.llm_client import GroqClient
from src.schemas import Run, RunStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def _score_in_background(
    repo: RunRepository, scoring_fn: ScoringFn, run_id: UUID
) -> None:
    """Run the scoring outside the request and persist the outcome (R8).

    Every terminal state is persisted: the result survives the HTTP request,
    the client tab and even process restarts.
    """
    run = repo.get(run_id)
    if run is None:  # pragma: no cover - defensive; run was just created
        logger.error("run %s vanished before scoring", run_id)
        return
    repo.update(run.model_copy(update={"status": RunStatus.SCORING}))
    try:
        final_state = run_scoring(run, scoring_fn)
    except Exception as exc:  # noqa: BLE001 - boundary by design (R8)
        repo.update(
            run.model_copy(
                update={"status": RunStatus.FAILED, "error_reason": f"{exc}"}
            )
        )
        logger.error("run %s scoring crashed: %s", run_id, exc)
        return
    if final_state.status is RunStatus.COMPLETED:
        repo.update(
            run.model_copy(
                update={"status": RunStatus.COMPLETED, "report": final_state.report}
            )
        )
    else:
        repo.update(
            run.model_copy(
                update={
                    "status": RunStatus.FAILED,
                    "error_reason": final_state.error_reason,
                }
            )
        )


def _load_run_or_404(repo: RunRepository, run_id: str) -> Run:
    """Fetch a run by id or raise 404 with a clear message (R5)."""
    try:
        parsed = UUID(str(run_id))
    except ValueError:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    run = repo.get(parsed)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return run


@router.post("/runs", status_code=201, response_model=CreateRunResponse)
def create_run(
    payload: CreateRunRequest,
    background: BackgroundTasks,
    repo: RunRepository = Depends(get_repo),
    scoring_fn: ScoringFn = Depends(get_scoring_fn),
) -> CreateRunResponse:
    """Persist a new pending run and start scoring in the background (R2)."""
    run = Run(call_type=payload.call_type, transcript=payload.transcript)
    repo.create(run)
    background.add_task(_score_in_background, repo, scoring_fn, run.run_id)
    return CreateRunResponse(
        run_id=run.run_id, url=f"/runs/{run.run_id}", status=run.status
    )


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: str, repo: RunRepository = Depends(get_repo)
) -> RunResponse:
    """Return the run status plus report or failure reason (R4, R5)."""
    run = _load_run_or_404(repo, run_id)
    return RunResponse(
        run_id=run.run_id,
        call_type=run.call_type,
        status=run.status,
        report=run.report,
        error_reason=run.error_reason,
        created_at=run.created_at,
    )


@router.get("/runs/{run_id}/report.pdf")
def get_report_pdf(
    run_id: str, repo: RunRepository = Depends(get_repo)
) -> Response:
    """Serve the rendered PDF for a completed run (R6, R7)."""
    from src.pdf_creation.report_pdf import PdfRenderError, render_pdf

    run = _load_run_or_404(repo, run_id)
    if run.status is not RunStatus.COMPLETED or run.report is None:
        reason = run.error_reason or "scoring has not finished yet"
        raise HTTPException(
            status_code=409,
            detail=f"report not available for run {run_id}: {reason}",
        )
    try:
        pdf_bytes = render_pdf(run.report)
    except PdfRenderError as exc:
        raise HTTPException(status_code=500, detail=f"report rendering failed: {exc}")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.pdf"'},
    )


__all__ = ["create_run", "get_report_pdf", "get_run", "router"]
