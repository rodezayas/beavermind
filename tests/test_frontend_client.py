"""Tests for the dashboard's API client (feature 10, R2-R8).

Every HTTP interaction is faked with `httpx.MockTransport`, so the suite runs
offline and asserts both the wire contract (what the client sends) and the
error mapping (what reason the UI will show).
"""

from uuid import uuid4

import httpx
import pytest

from src.frontend.api_client import ApiClientError, ScoringApiClient
from src.schemas import CallType, RunStatus

#: A syntactically valid run id used across the fake responses
RUN_ID = "11111111-2222-3333-4444-555555555555"


def _client_for(handler) -> ScoringApiClient:
    """Build a `ScoringApiClient` backed by a MockTransport handler."""
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    return ScoringApiClient("http://test", client=http)


def test_create_run_sends_transcript_and_call_type():
    """R1/R2: POST /runs carries the transcript and call type in the body."""
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["json"] = request.read().decode()
        return httpx.Response(
            201,
            json={"run_id": RUN_ID, "url": f"/runs/{RUN_ID}", "status": "pending"},
        )

    client = _client_for(handler)
    created = client.create_run("hello world transcript", CallType.KICKOFF)

    import json as jsonlib

    body = jsonlib.loads(seen["json"])
    assert seen["method"] == "POST"
    assert seen["path"] == "/runs"
    assert body == {"transcript": "hello world transcript", "call_type": "kickoff"}
    assert str(created.run_id) == RUN_ID
    assert created.url == f"/runs/{RUN_ID}"
    assert created.status is RunStatus.PENDING


def test_run_url_and_status_shown():
    """R2: the created run exposes its unique URL and initial status."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            201,
            json={"run_id": RUN_ID, "url": f"/runs/{RUN_ID}", "status": "scoring"},
        )

    created = _client_for(handler).create_run("t", CallType.COACHING)
    assert created.status is RunStatus.SCORING


def test_get_run_completed_returns_report():
    """R3/R6: GET /runs/{id} maps the stored report without re-scoring."""
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(
            200,
            json={
                "run_id": RUN_ID,
                "call_type": "kickoff",
                "status": "completed",
                "report": None,  # full report shape is covered by domain tests
                "error_reason": None,
                "created_at": "2026-08-24T10:00:00Z",
            },
        )

    run = _client_for(handler).get_run(RUN_ID)
    assert run.run_id == __import__("uuid").UUID(RUN_ID)
    assert run.status is RunStatus.COMPLETED


def test_failed_reason_surfaced():
    """R4: a failed run carries the API-provided error_reason."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "run_id": RUN_ID,
                "call_type": "coaching",
                "status": "failed",
                "report": None,
                "error_reason": "transcript too short to score",
                "created_at": "2026-08-24T10:00:00Z",
            },
        )

    run = _client_for(handler).get_run(RUN_ID)
    assert run.status is RunStatus.FAILED
    assert run.error_reason == "transcript too short to score"


def test_pdf_download_url_and_bytes():
    """R5: download_pdf returns the raw bytes from report.pdf."""
    pdf_bytes = b"%PDF-1.4 fake"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/runs/{RUN_ID}/report.pdf"
        return httpx.Response(200, content=pdf_bytes)

    assert _client_for(handler).download_pdf(RUN_ID) == pdf_bytes


def test_api_error_reason_propagated_422():
    """R7: a validation failure surfaces the API's structured detail."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={"detail": [{"loc": ["body", "call_type"], "msg": "invalid choice"}]},
        )

    with pytest.raises(ApiClientError) as excinfo:
        _client_for(handler).create_run("valid transcript", CallType.KICKOFF)
    assert "call_type" in excinfo.value.reason
    assert excinfo.value.status_code == 422


def test_empty_transcript_is_rejected_with_a_reason():
    """R7: an empty transcript fails client-side with a clear reason."""
    with pytest.raises(ApiClientError) as excinfo:
        _client_for(lambda request: httpx.Response(201)).create_run("", CallType.KICKOFF)
    assert "transcript" in excinfo.value.reason
    assert excinfo.value.status_code is None  # never reached the API


def test_api_error_reason_propagated_409_pdf_not_ready():
    """R7: a 409 on the PDF endpoint explains why it is unavailable."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={"detail": "report not available: scoring has not finished yet"},
        )

    with pytest.raises(ApiClientError) as excinfo:
        _client_for(handler).download_pdf(uuid4())
    assert "not available" in excinfo.value.reason


def test_unknown_run_maps_to_clear_error():
    """R5/R7: a 404 for an unknown run keeps the API's message."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": f"run {RUN_ID} not found"})

    with pytest.raises(ApiClientError) as excinfo:
        _client_for(handler).get_run(RUN_ID)
    assert "not found" in excinfo.value.reason


def test_transport_failure_is_mapped():
    """R7: network-level failures become ApiClientError with a reason."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(ApiClientError) as excinfo:
        _client_for(handler).get_run(RUN_ID)
    assert "could not reach the API" in excinfo.value.reason


def test_non_json_error_body_still_yields_a_reason():
    """R7: even an HTML/plain-text error never produces a silent failure."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="<html>boom</html>")

    with pytest.raises(ApiClientError) as excinfo:
        _client_for(handler).get_run(RUN_ID)
    assert "500" in excinfo.value.reason
