"""Streamlit dashboard for the scoring operator (feature 10, Opción A).

Flow: paste a transcript, pick the evaluation type (kick-off | coaching),
submit, watch the run status live, and read/download the report. A finished
run can also be reopened later by its id without re-scoring (R6).

The look follows `design-mocks/`: a cream, card-based "Run an evaluation"
home and a report view with a score arc, band pill, red-flag chips and
numbered dimension rows.
"""

import html
import os
import sys
import time
from pathlib import Path
from uuid import UUID

import streamlit as st

# Streamlit puts the script's own directory (src/frontend/) on sys.path, not
# the project root; prepend the root so `src.*` package imports resolve when
# launched via `streamlit run src/frontend/app.py`.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.frontend.api_client import ApiClientError, ScoringApiClient  # noqa: E402
from src.schemas import CallType, RunStatus  # noqa: E402

#: Seconds between status polls while the run is pending/scoring (R2)
POLL_INTERVAL_SECONDS = 2.0

#: Card picker options: label shown on the card -> `CallType` value
CALL_TYPE_CARDS: dict[str, CallType] = {
    "Kick-off call": CallType.KICKOFF,
    "Coaching call": CallType.COACHING,
}

#: Colors per rubric band (Elite → Fail), used in pills and the score arc
BAND_COLORS: dict[str, str] = {
    "Elite": "#1E7F4F",
    "Strong": "#5B8C5A",
    "Inconsistent": "#C98A1B",
    "At risk": "#C0392B",
    "Fail": "#8B1E1E",
}

#: Neutral color for the unfilled part of the score arc
_ARC_TRACK = "#ECE8E1"

#: Design tokens shared by the CSS theme and inline HTML widgets
_INK = "#1F1D1A"  # primary text
_MUTED = "#8B867E"  # secondary text
_BORDER = "#E7E3DC"  # card borders
_CARD = "#FFFFFF"  # card fill
_BG = "#FAF8F4"  # page background

_CSS = f"""
<style>
    /* Page canvas: warm off-white like the mocks */
    .stApp {{ background: {_BG}; color: {_INK}; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* Uppercase micro-label used above form sections */
    .field-label {{
        font-size: 0.68rem; letter-spacing: 0.14em; font-weight: 600;
        text-transform: uppercase; color: {_MUTED}; margin: 0 0 0.3rem 0;
    }}

    /* Type-picker cards (Kick-off / Coaching) */
    div[data-testid="stVerticalBlockBorder-rounded"] {{ background: {_CARD}; }}
    .type-card {{
        border: 1px solid {_BORDER}; border-radius: 12px; background: {_CARD};
        padding: 1.4rem 1rem; text-align: center; height: 100%;
    }}
    .type-card .icon {{ font-size: 1.5rem; }}
    .type-card .name {{ font-weight: 600; margin-top: 0.5rem; }}
    .type-card .hint {{ color: {_MUTED}; font-size: 0.8rem; margin-top: 0.2rem; }}

    /* Report header card */
    .report-card {{
        border: 1px solid {_BORDER}; border-radius: 14px; background: {_CARD};
        padding: 1.2rem 1.4rem;
    }}
    .eyebrow {{
        font-size: 0.68rem; letter-spacing: 0.16em; font-weight: 600;
        text-transform: uppercase; color: {_MUTED};
    }}
    .run-title {{ font-size: 1.35rem; font-weight: 700; margin: 0.2rem 0 0 0; }}
    .run-sub {{ color: {_MUTED}; font-size: 0.85rem; margin-top: 0.2rem; }}

    /* The One Thing: big editorial quote */
    .one-thing {{
        font-size: 1.45rem; line-height: 1.35; font-weight: 600;
        margin: 1.4rem 0 0.4rem 0;
    }}
    .projected {{ color: {_MUTED}; font-size: 0.9rem; }}

    /* Red-flag chips */
    .flag-chip {{
        display: inline-block; background: #FBEAE8; color: #9C2B1F;
        border-radius: 8px; padding: 0.35rem 0.7rem; font-size: 0.82rem;
        margin: 0.25rem 0.25rem 0 0;
    }}

    /* Band pill under the score arc */
    .band-pill {{
        display: inline-block; border-radius: 999px; padding: 0.25rem 0.8rem;
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: #FFFFFF;
    }}

    /* Dimension rows */
    .dim-row {{ border-top: 1px solid {_BORDER}; padding: 0.9rem 0.2rem; }}
    .dim-num {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 1.5rem; height: 1.5rem; border-radius: 50%;
        border: 1px solid {_BORDER}; font-size: 0.75rem; color: {_MUTED};
        margin-right: 0.6rem;
    }}
    .dim-title {{ font-weight: 600; }}
    .score-chip {{
        float: right; background: #F1EEE8; border-radius: 999px;
        padding: 0.2rem 0.7rem; font-size: 0.8rem; font-weight: 600;
    }}
    .dim-reasoning {{ color: #4A4741; font-size: 0.88rem; margin-top: 0.45rem; }}
    .dim-disabled {{ color: {_MUTED}; font-size: 0.85rem; font-style: italic; }}

    /* Evidence quotes inside the details expander */
    .evidence {{
        border-left: 3px solid {_BORDER}; margin: 0.3rem 0; padding: 0.15rem 0.8rem;
        color: {_MUTED}; font-size: 0.85rem; font-style: italic;
    }}

    /* Primary action button: dark, pill-shaped */
    .stButton > button[kind="primary"] {{
        background: {_INK}; border: 1px solid {_INK}; border-radius: 999px;
        color: #FFFFFF; padding: 0.45rem 1.6rem; font-weight: 600;
    }}
    .stButton > button[kind="secondary"] {{
        border-radius: 999px; font-weight: 600;
    }}
</style>
"""


def _esc(text: str) -> str:
    """HTML-escape model/report text before embedding it in markup."""
    return html.escape(str(text))


def _client() -> ScoringApiClient:
    """Build the API client from the SCORING_API_URL environment variable.

    Returns:
        A client whose base URL is normalized (scheme added when missing),
        so a bare hostname injected by the platform still works.
    """
    base_url = os.environ.get("SCORING_API_URL", "http://localhost:8000")
    return ScoringApiClient(base_url)


def _run_url(run_id: str) -> str:
    """Build the persistent, shareable URL of one run.

    The report lives in Supabase, so the URL keeps working after closing the
    tab, in another browser, or days later — it never expires.

    Args:
        run_id: The run identifier.

    Returns:
        An absolute dashboard URL like `https://<host>/?run_id=<uuid>`
        (plain `http://` only when serving from a local host).
    """
    host = "localhost:8501"
    try:  # st.context is only available while serving a real request
        host = st.context.headers.get("Host", host)
    except Exception:
        pass  # fallback host keeps the URL usable in bare scripts/tests
    hostname = host.split(":", 1)[0].lower()  # strip the port for the check
    scheme = "http" if hostname in ("localhost", "127.0.0.1") else "https"
    return f"{scheme}://{host}/?run_id={run_id}"


def _report_view(client: ScoringApiClient, run_id: str) -> None:
    """Render one run addressed by its persistent URL (`?run_id=<uuid>`).

    This is the landing view for a shared/bookmarked run URL: it fetches the
    stored run without re-scoring (R6) and shows the report, the failure
    reason, or the live status while still scoring.
    """
    if st.button("← Back to home"):
        st.query_params.clear()
        st.rerun()
    try:
        run = client.get_run(run_id)
    except ApiClientError as exc:
        st.error(f"Could not fetch the run: {exc.reason}")
        return
    st.code(_run_url(str(run.run_id)), language=None)  # the persistent URL (R2)
    if run.status is RunStatus.FAILED:
        st.error(f"❌ The run failed: {run.error_reason}")  # R4
    elif run.status is RunStatus.COMPLETED:
        _render_report(run)
        _pdf_button(client, str(run.run_id))  # R5
    else:
        st.info(f"Run status: **{run.status.value}** — this URL stays valid; "
                "reload it in a moment to see the result.")


def _score_arc(total: float, max_possible: float, band: str) -> str:
    """Build the semicircular score gauge as inline SVG (mock: 67/100 + band).

    Args:
        total: Grade total achieved by the run.
        max_possible: Maximum possible grade for the rubric (100 or 85).
        band: Rubric band name; drives the arc and pill color.

    Returns:
        HTML markup with the gauge and the band pill beneath it.
    """
    color = BAND_COLORS.get(band, _INK)
    radius = 65  # arc radius in SVG units
    arc_length = 3.14159 * radius  # semicircle length
    fraction = max(0.0, min(1.0, total / max_possible if max_possible else 0.0))
    filled = arc_length * fraction
    return f"""
    <div style="text-align:center">
      <svg width="170" height="100" viewBox="0 0 170 100">
        <path d="M 20 90 A {radius} {radius} 0 0 1 150 90"
              fill="none" stroke="{_ARC_TRACK}" stroke-width="12" stroke-linecap="round"/>
        <path d="M 20 90 A {radius} {radius} 0 0 1 150 90"
              fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"
              stroke-dasharray="{filled:.1f} {arc_length:.1f}"/>
        <text x="85" y="78" text-anchor="middle" font-size="34" font-weight="700"
              fill="{_INK}">{total:g}</text>
        <text x="85" y="96" text-anchor="middle" font-size="12"
              fill="{_MUTED}">/{max_possible:g}</text>
      </svg><br/>
      <span class="band-pill" style="background:{color}">{_esc(band)}</span>
    </div>
    """


#: Consecutive polling failures tolerated before giving up (free-tier cold
#: starts can briefly refuse connections while the API instance boots)
MAX_POLL_FAILURES = 10


def _poll_until_done(client: ScoringApiClient, run_id: UUID) -> None:
    """Poll GET /runs/{id} until terminal state, updating the status UI (R2).

    Transient transport failures (e.g. the free-tier API waking up) do not
    abort the poll: only after `MAX_POLL_FAILURES` consecutive errors does
    it surface a reason.
    """
    status_box = st.empty()
    spinner = st.spinner("Scoring in progress…")
    spinner.__enter__()
    consecutive_failures = 0
    try:
        while True:
            try:
                run = client.get_run(run_id)
                consecutive_failures = 0
            except ApiClientError as exc:
                consecutive_failures += 1
                if consecutive_failures >= MAX_POLL_FAILURES:
                    st.error(
                        f"Could not fetch the run status after "
                        f"{consecutive_failures} attempts: {exc.reason}"
                    )
                    return
                time.sleep(POLL_INTERVAL_SECONDS)
                continue
            if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
                return
            status_box.info(f"Run status: **{run.status.value}**…")
            time.sleep(POLL_INTERVAL_SECONDS)
    finally:
        spinner.__exit__(None, None, None)


def _render_report(run) -> None:
    """Render a completed run's report and the PDF download button (R3, R5).

    Layout mirrors `design-mocks/After Score.png`: header card, editorial
    quote for the One Thing, brief, red-flag chips, score gauge with band and
    numbered dimension rows with score chips.
    """
    report = run.report
    assert report is not None  # guaranteed by the API contract for completed runs
    grade = report.grade

    # --- Header card: eyebrow, run identity and score gauge side by side ----
    left, right = st.columns([3, 1], vertical_alignment="center")
    with left:
        st.markdown(
            f"""
            <div class="report-card">
              <div class="eyebrow">Full analysis &nbsp;·&nbsp; {_esc(run.call_type.value)} call</div>
              <div class="run-title">Run {_esc(str(run.run_id)[:8])}</div>
              <div class="run-sub">Scored against the {_esc(run.call_type.value)} rubric
              · {_esc(run.created_at.strftime("%Y-%m-%d %H:%M UTC"))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(_score_arc(grade.total, grade.max_possible, grade.band), unsafe_allow_html=True)

    # --- The One Thing: headline quote + projected score --------------------
    st.markdown(f'<div class="one-thing">“{_esc(report.one_thing.change)}”</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="projected">Projected score with the change applied: '
        f'<b>{report.one_thing.projected_score:g}</b></div>',
        unsafe_allow_html=True,
    )

    # --- Brief ---------------------------------------------------------------
    st.markdown(f'<div class="dim-reasoning">{_esc(report.brief)}</div>', unsafe_allow_html=True)

    # --- Red flags as chips ---------------------------------------------------
    if report.red_flags:
        chips = "".join(
            f'<span class="flag-chip">🚩 {_esc(flag)}</span>' for flag in report.red_flags
        )
        st.markdown(f'<div style="margin-top:0.8rem">{chips}</div>', unsafe_allow_html=True)

    # --- Dimension rows -------------------------------------------------------
    st.markdown(
        '<div class="field-label" style="margin-top:1.6rem">Dimensions</div>',
        unsafe_allow_html=True,
    )
    for index, dim in enumerate(report.dimensions, start=1):
        with st.container():
            if dim.disabled:
                # Optional dimension that did not occur: no score to show
                st.markdown(
                    f'<div class="dim-row">'
                    f'<span class="score-chip" style="float:right">N/A</span>'
                    f'<span class="dim-num">{index}</span>'
                    f'<span class="dim-title">D{dim.dimension_id}. {_esc(dim.name)}</span>'
                    f'<div class="dim-disabled">Disabled — {_esc(dim.disabled_reason or "")}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="dim-reasoning">{_esc(dim.reasoning)}</div>', unsafe_allow_html=True)
                continue
            color = BAND_COLORS.get(dim.band or "", _MUTED)
            st.markdown(
                f'<div class="dim-row">'
                f'<span class="score-chip" style="float:right">'
                f'{dim.score:g}/{dim.max_points:g}</span>'
                f'<span class="dim-num">{index}</span>'
                f'<span class="dim-title">D{dim.dimension_id}. {_esc(dim.name)}</span>'
                f'<span class="band-pill" style="background:{color};margin-left:0.6rem;'
                f'font-size:0.6rem;padding:0.15rem 0.55rem">{_esc(dim.band or "")}</span>'
                f'<div class="dim-reasoning">{_esc(dim.reasoning)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            with st.expander("Evidence & quick fix"):
                for line in dim.transcript_lines or []:
                    st.markdown(f'<div class="evidence">“{_esc(line)}”</div>', unsafe_allow_html=True)
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
        "⬇ Download PDF",
        data=cache[run_id],
        file_name=f"{run_id}.pdf",
        mime="application/pdf",
    )


def _home_view(client: ScoringApiClient) -> None:
    """Render the 'Run an evaluation' home (mock: design-mocks/UI.png).

    Flow is sequential: the operator first picks the call type (which selects
    the rubric) and only then the transcript field appears.
    """
    st.markdown("## Run an evaluation")
    st.markdown('<div class="run-sub">Score one call at a time against its rubric.</div>', unsafe_allow_html=True)
    # Show where requests actually go, so a misrouted SCORING_API_URL is
    # visible at a glance instead of failing silently on submit.
    st.caption(f"Scoring API: `{client.base_url}`")

    selected: CallType | None = st.session_state.get("selected_call_type")

    # --- Step 1: type picker — one card per rubric (mock's call-type cards) --
    st.markdown(
        '<div class="field-label" style="margin-top:1.2rem">Choose the call to evaluate</div>',
        unsafe_allow_html=True,
    )
    card_cols = st.columns(len(CALL_TYPE_CARDS))
    for col, (label, call_type) in zip(card_cols, CALL_TYPE_CARDS.items()):
        with col:
            is_selected = selected is call_type
            border = f"2px solid {_INK}" if is_selected else f"1px solid {_BORDER}"
            icon = "🚀" if call_type is CallType.KICKOFF else "🎯"
            st.markdown(
                f'<div class="type-card" style="border:{border}">'
                f'<div class="icon">{icon}</div>'
                f'<div class="name">{label}</div>'
                f'<div class="hint">{call_type.value} rubric</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            button_label = (
                f"✓ {label} selected" if is_selected else f"Run {label.split()[0]} →"
            )
            if st.button(button_label, key=f"card_{call_type.value}"):
                st.session_state["selected_call_type"] = call_type
                st.rerun()

    # --- Step 2: transcript, only after the rubric is chosen ------------------
    if selected is None:
        st.info("Pick a call type above to continue.")
        return
    back_col, _ = st.columns([1, 3])
    if back_col.button("← Change call type"):
        del st.session_state["selected_call_type"]
        st.rerun()

    st.markdown('<div class="field-label" style="margin-top:1rem">Call transcript</div>', unsafe_allow_html=True)
    transcript = st.text_area(
        "Transcript",
        height=280,
        label_visibility="collapsed",
        placeholder="Paste the call transcript here…",
    )

    if st.button("Evaluate", type="primary", disabled=not transcript.strip()):
        try:
            created = client.create_run(transcript, selected)
        except ApiClientError as exc:
            st.error(f"The run could not be created: {exc.reason}")  # R7
            st.stop()
        st.session_state["current_run_id"] = str(created.run_id)
        st.code(_run_url(str(created.run_id)), language=None)  # persistent URL (R2)
        _poll_until_done(client, created.run_id)
        st.rerun()

    # --- Outcome of the current run -------------------------------------------
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
            _render_report(run)
            _pdf_button(client, str(run.run_id))  # R5
        else:
            st.info(f"Run status: {run.status.value}")

    # --- Reopen a stored run (R6) ----------------------------------------------
    st.divider()
    st.markdown('<div class="field-label">Open an existing run</div>', unsafe_allow_html=True)
    id_col, load_col = st.columns([4, 1], vertical_alignment="bottom")
    raw = id_col.text_input(
        "Run id or URL", label_visibility="collapsed", placeholder="Paste a run id or URL…"
    )
    if load_col.button("Open run"):
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
        st.session_state["current_run_id"] = str(run.run_id)
        if run.status is RunStatus.FAILED:
            st.error(f"❌ The run failed: {run.error_reason}")
        elif run.status is RunStatus.COMPLETED:
            _render_report(run)
            _pdf_button(client, str(run.run_id))
        else:
            st.info("This run has not finished yet; come back later.")


def main() -> None:
    """Entry point of the Streamlit dashboard.

    A `?run_id=<uuid>` query parameter turns the app into a per-run landing
    page: the persistent URL of a run renders its stored report directly,
    even days later and from another browser (the report lives in Supabase).
    """
    st.set_page_config(page_title="Call Scoring", page_icon="📊", layout="centered")
    st.markdown(_CSS, unsafe_allow_html=True)
    client = _client()
    query_run_id = st.query_params.get("run_id")
    if query_run_id:
        _report_view(client, str(query_run_id))
    else:
        _home_view(client)


if __name__ == "__main__":
    main()
