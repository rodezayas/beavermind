"""Streamlit dashboard for the scoring operator (feature 10, Opción A).

Flow: paste a transcript, pick the evaluation type (kick-off | coaching),
submit, watch the run status live, and read/download the report. A finished
run can also be reopened later by its id without re-scoring (R6).
"""

import os
import time
from uuid import UUID

import streamlit as st

from src.frontend.api_client import ApiClientError, ScoringApiClient
from src.schemas import CallType, RunStatus

#: Seconds between status polls while the run is pending/scoring (R2)
POLL_INTERVAL_SECONDS = 2.0

#: Labels for the two supported evaluation types; value maps to `CallType`
CALL_TYPE_OPTIONS: dict[str, str] = {
    "🚀 Kick-off Call": CallType.KICKOFF.value,
    "🎯 Coaching Call": CallType.COACHING.value,
}


def _client() -> ScoringApiClient:
    """Build the API client from the SCORING_API_URL environment variable."""
    base_url = os.environ.get("SCORING_API_URL", "http://localhost:8000")
    return ScoringApiClient(base_url)


def _poll_until_done(client: ScoringApiClient, run_id: UUID) -> None:
    """Poll GET /runs/{id} until terminal state, updating the status UI (R2)."""
    status_box = st.empty()
    spinner = st.spinner("Scoring in progress…")
    spinner.__enter__()
    try:
        while True:
            try:
                run = client.get_run(run_id)
            except ApiClientError as exc:
                st.error(f"Could not fetch the run status: {exc.reason}")
                return
            if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
                return
            status_box.info(f"Run status: **{run.status.value}**…")
            time.sleep(POLL_INTERVAL_SECONDS)
    finally:
        spinner.__exit__(None, None, None)


def _render_report(run) -> None:
    """Render a completed run's report and the PDF download button (R3, R5).

    Args:
        run: A `RunResponse` with `status == completed` and a populated report.
    """
    report = run.report
    assert report is not None  # guaranteed by the API contract for completed runs

    st.subheader(f"Grade: {report.grade.total:g} / {report.grade.max_possible:g}")
    st.badge(report.grade.band)

    st.subheader("The One Thing")
    st.markdown(
        f"**{report.one_thing.change}**\n\n"
        f"Projected score with the change applied: "
        f"**{report.one_thing.projected_score:g}**"
    )

    st.subheader("Brief")
    st.write(report.brief)

    if report.red_flags:
        st.subheader("Red flags")
        for flag in report.red_flags:
            st.markdown(f"- 🚩 {flag}")

    st.subheader("Dimensions")
    for dim in report.dimensions:
        if dim.disabled:
            header = f"D{dim.dimension_id}. {dim.name} — disabled"
        else:
            header = f"D{dim.dimension_id}. {dim.name} — {dim.score:g}/{dim.max_points}"
        with st.expander(header, expanded=False):
            if dim.disabled:
                st.caption(dim.disabled_reason)
                st.write(dim.reasoning)
                continue
            st.badge(dim.band or "")
            st.write(dim.reasoning)
            if dim.transcript_lines:
                st.caption("Evidence:")
                for line in dim.transcript_lines:
                    st.markdown(f"> {line}")
            st.success(f"Quick fix: {dim.quick_fix}")


def _pdf_button(client: ScoringApiClient, run_id: str) -> None:
    """Offer the PDF download for a completed run (R5).

    The bytes are cached in session state so re-renders don't refetch.
    """
    cache: dict[str, bytes] = st.session_state.setdefault("pdf_cache", {})
    if run_id not in cache:
        try:
            cache[run_id] = client.download_pdf(run_id)
        except ApiClientError as exc:
            st.error(f"PDF is not available: {exc.reason}")
            return
    st.download_button(
        "⬇️ Download PDF report",
        data=cache[run_id],
        file_name=f"{run_id}.pdf",
        mime="application/pdf",
    )


def main() -> None:
    """Entry point of the Streamlit dashboard."""
    st.set_page_config(page_title="Call Scoring", page_icon="📊", layout="centered")
    st.title("📊 Call Scoring Dashboard")

    client = _client()

    tab_new, tab_existing = st.tabs(["New evaluation", "Open an existing run"])

    with tab_new:
        # R1: transcript + call type must both be provided before submitting
        call_type_label = st.radio(
            "Evaluation type",
            options=list(CALL_TYPE_OPTIONS),
            horizontal=True,
            help="Kick-off and coaching calls use different rubrics.",
        )
        call_type = CallType(CALL_TYPE_OPTIONS[call_type_label])
        transcript = st.text_area(
            "Call transcript",
            height=300,
            placeholder="Paste the call transcript here…",
        )

        if st.button("Evaluate", type="primary", disabled=not transcript.strip()):
            try:
                created = client.create_run(transcript, call_type)
            except ApiClientError as exc:
                st.error(f"The run could not be created: {exc.reason}")  # R7
                st.stop()
            st.session_state["current_run_id"] = str(created.run_id)
            st.code(created.url, language=None)  # unique persistent URL (R2)
            _poll_until_done(client, created.run_id)
            st.rerun()

        # Render outcome after polling or on rerun of a known run
        run_id = st.session_state.get("current_run_id")
        if run_id:
            try:
                run = client.get_run(run_id)
            except ApiClientError as exc:
                st.error(f"Could not fetch the run: {exc.reason}")
                return
            if run.status is RunStatus.FAILED:
                st.error(f"❌ The run failed: {run.error_reason}")  # R4
            elif run.status is RunStatus.COMPLETED:
                st.success("✅ Scoring completed")
                _render_report(run)
                _pdf_button(client, str(run.run_id))  # R5
            else:
                st.info(f"Run status: {run.status.value}")

    with tab_existing:
        # R6: reopen any stored run by id/URL without re-running the scoring
        raw = st.text_input("Run id or URL", placeholder="e.g. /runs/<uuid> or <uuid>")
        if st.button("Load run"):
            candidate = raw.strip().rstrip("/").split("/")[-1]
            try:
                UUID(candidate)  # validate shape before calling the API
            except ValueError:
                st.error("That does not look like a valid run id.")
                st.stop()
            try:
                run = client.get_run(candidate)
            except ApiClientError as exc:
                st.error(exc.reason)  # e.g. "run <uuid> not found" (R5/R7)
                st.stop()
            st.write(f"Call type: **{run.call_type.value}** — status: **{run.status.value}**")
            if run.status is RunStatus.FAILED:
                st.error(f"❌ The run failed: {run.error_reason}")
            elif run.status is RunStatus.COMPLETED:
                _render_report(run)
                _pdf_button(client, str(run.run_id))
            else:
                st.info("This run has not finished yet; come back later.")


if __name__ == "__main__":
    main()
