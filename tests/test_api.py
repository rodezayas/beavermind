"""Tests for the FastAPI surface (feature: api_fastapi).

Uses the app factory with an in-memory repository, a GroqClient over a fake
transport, and the real scoring function wired to a stubbed LLM reply — no
network, no credentials.
"""

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.config import Settings
from src.database.repository import InMemoryRunRepository
from src.llm_client import GroqClient
from src.schemas import CallType, RunStatus

SETTINGS = Settings(
    groq_api_key="test-key",
    supabase_project_id="p",
    supabase_api_key="a",
    supabase_secret_key="s",
    database="db",
)

TRANSCRIPT = "\n".join(f"[Speaker {i}]: line {i}" for i in range(1, 7))


def _llm_json_reply() -> str:
    """LLM reply satisfying the scoring JSON contract for kickoff."""
    dimensions = [
        {"dimension_id": i, "score": 4, "band": "Strong",
         "reasoning": "quote-first", "transcript_lines": ["[Speaker 1]: line 1"],
         "quick_fix": "push", "cap_fired": False}
        for i in range(1, 13)
    ]
    payload = {
        "one_thing": {"change": "book live", "projected_score": 90},
        "brief": "Good call.",
        "red_flags": ["no booking"],
        "dimensions": dimensions,
    }
    return json.dumps({"choices": [{"message": {"content": json.dumps(payload)}}]})


class _FakeTransport:
    """Transport stub returning a canned reply."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[dict] = []

    def post(self, url, headers, payload):
        self.calls.append(payload)
        return 200, self.reply


def _scoring_fn_factory(transport: _FakeTransport):
    """Real scoring pipeline (build_report) over the stubbed LLM."""
    from src.rubrics import load_rubric
    from src.scoring import build_prompt, build_report

    def scoring_fn(call_type: CallType, transcript: str):
        rubric = load_rubric(call_type)
        client = GroqClient(settings=SETTINGS, transport=transport)
        output = client.complete_json(build_prompt(call_type, transcript, rubric))
        return build_report(output, rubric)

    return scoring_fn


def _client(transport: _FakeTransport | None = None, repo=None) -> TestClient:
    transport = transport or _FakeTransport(_llm_json_reply())
    app = create_app(
        repo=repo or InMemoryRunRepository(),
        llm=GroqClient(settings=SETTINGS, transport=transport),
        scoring_fn=_scoring_fn_factory(transport),
    )
    return TestClient(app)


# --- R1 / R2 / R3: create run ------------------------------------------------


def test_app_factory_with_fakes():
    client = _client()
    response = client.post(
        "/runs", json={"transcript": TRANSCRIPT, "call_type": "kickoff"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["url"].startswith("/runs/")
    assert body["status"] == "pending"


def test_post_run_creates_and_scores():
    transport = _FakeTransport(_llm_json_reply())
    with _client(transport) as client:  # context runs background tasks
        response = client.post(
            "/runs", json={"transcript": TRANSCRIPT, "call_type": "kickoff"}
        )
        run_id = response.json()["run_id"]
        final = client.get(f"/runs/{run_id}")
    assert final.json()["status"] == "completed"
    assert final.json()["report"]["grade"]["band"] in {
        "Elite", "Strong", "Inconsistent", "At risk", "Fail"
    }
    assert len(transport.calls) == 1  # exactly one LLM call


def test_post_run_invalid_body():
    client = _client()
    empty = client.post("/runs", json={"transcript": "", "call_type": "kickoff"})
    assert empty.status_code == 422
    unknown = client.post(
        "/runs", json={"transcript": TRANSCRIPT, "call_type": "webinar"}
    )
    assert unknown.status_code == 422


# --- R4 / R5: get run --------------------------------------------------------


def test_get_run_completed_returns_report():
    with _client() as client:
        run_id = client.post(
            "/runs", json={"transcript": TRANSCRIPT, "call_type": "kickoff"}
        ).json()["run_id"]
        body = client.get(f"/runs/{run_id}").json()
    assert body["status"] == "completed"
    assert body["report"]["one_thing"]["change"] == "book live"
    assert len(body["report"]["dimensions"]) == 12


def test_get_run_failed_returns_reason():
    repo = InMemoryRunRepository()
    client = _client(repo=repo)
    run_id = client.post(
        "/runs", json={"transcript": "too short", "call_type": "kickoff"}
    ).json()["run_id"]
    with client:
        client.get(f"/runs/{run_id}")
    body = client.get(f"/runs/{run_id}").json()
    assert body["status"] == "failed"
    assert "speaker turns" in body["error_reason"]


def test_get_run_not_found():
    response = _client().get(f"/runs/{uuid4()}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# --- R6 / R7: PDF endpoint ---------------------------------------------------


def test_pdf_endpoint_returns_attachment():
    with _client() as client:
        run_id = client.post(
            "/runs", json={"transcript": TRANSCRIPT, "call_type": "kickoff"}
        ).json()["run_id"]
        pdf = client.get(f"/runs/{run_id}/report.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf.headers["content-disposition"]
    assert pdf.content.startswith(b"%PDF")


def test_pdf_endpoint_conflicts_when_not_completed():
    client = _client()
    run_id = client.post(
        "/runs", json={"transcript": "too short", "call_type": "kickoff"}
    ).json()["run_id"]
    with client:
        client.get(f"/runs/{run_id}")  # let the background task fail it
    response = client.get(f"/runs/{run_id}/report.pdf")
    assert response.status_code == 409
    assert "not available" in response.json()["detail"]


# --- R8 / R9: persistence & secrets -----------------------------------------


def test_background_outcome_persisted():
    """The outcome lives in the repository, not in request state (R8)."""
    repo = InMemoryRunRepository()
    with _client(repo=repo) as client:
        run_id = client.post(
            "/runs", json={"transcript": TRANSCRIPT, "call_type": "coaching"}
        ).json()["run_id"]
    # After the request (tab closed), the run is still retrievable.
    from uuid import UUID

    run = repo.get(UUID(run_id))
    assert run.status is RunStatus.COMPLETED
    assert run.report is not None


def test_error_messages_contain_no_secrets():
    client = _client()
    probe = client.get(f"/runs/{uuid4()}")
    text = probe.text.lower()
    for secret in ("test-key", "groq_api_key", "supabase", "secret"):
        assert secret not in text


# --- SCORING_MODE=sync --------------------------------------------------------


def test_sync_mode_returns_terminal_status(monkeypatch):
    """With SCORING_MODE=sync the 201 response already carries the outcome."""
    monkeypatch.setenv("SCORING_MODE", "sync")
    transport = _FakeTransport(_llm_json_reply())
    client = _client(transport)
    response = client.post(
        "/runs", json={"transcript": TRANSCRIPT, "call_type": "kickoff"}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "completed"  # no pending: scored inline
    run_id = response.json()["run_id"]
    final = client.get(f"/runs/{run_id}")
    assert final.json()["status"] == "completed"
    assert final.json()["report"] is not None
