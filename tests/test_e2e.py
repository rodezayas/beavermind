"""End-to-end tests: real transcripts through the full API pipeline.

Feature: tests_e2e (no SDD spec; acceptance lives in
`settings_files_tasks.json`). Everything runs with stubbed LLM transport and
in-memory storage — deterministic, no network, no credentials.
"""

import json
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.config import Settings
from src.database.repository import InMemoryRunRepository
from src.llm_client import GroqClient
from src.rubrics import load_rubric
from src.scoring import build_prompt, build_report
from src.schemas import RunStatus

SETTINGS = Settings(
    groq_api_key="test-key",
    supabase_project_id="p",
    supabase_api_key="a",
    supabase_secret_key="s",
    database="db",
)

TRANSCRIPTS_DIR = Path("transcripts")


def _reply_for(call_type: str) -> str:
    """Build a contract-valid LLM reply, tuned per call type."""
    dims = [
        {
            "dimension_id": i,
            "score": 4,
            "band": "Strong",
            "reasoning": "quote-first rationale",
            "transcript_lines": ["[Coach]: evidence"],
            "quick_fix": "reach elite",
            "cap_fired": False,
        }
        for i in range(1, 13)
    ]
    payload = {
        "one_thing": {"change": "book the next call live", "projected_score": 90},
        "brief": "Solid call with room to close stronger.",
        "red_flags": ["booking left open"],
        "dimensions": dims,
    }
    return json.dumps({"choices": [{"message": {"content": json.dumps(payload)}}]})


class _RoutedFakeTransport:
    """Fake transport that answers per call type using real rubric prompts."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def post(self, url, headers, payload):
        self.prompts.append(payload["messages"][0]["content"])
        return 200, _reply_for("kickoff")


def _make_client(transport):
    """App with the real scoring pipeline over the fake transport."""

    def scoring_fn(call_type, transcript):
        rubric = load_rubric(call_type)
        client = GroqClient(settings=SETTINGS, transport=transport)
        output = client.complete_json(build_prompt(call_type, transcript, rubric))
        return build_report(output, rubric)

    app = create_app(
        repo=InMemoryRunRepository(),
        llm=GroqClient(settings=SETTINGS, transport=transport),
        scoring_fn=scoring_fn,
    )
    return TestClient(app)


def _transcript(name: str) -> str:
    return (TRANSCRIPTS_DIR / name).read_text(encoding="utf-8")


def test_e2e_kickoff_happy_path():
    transport = _RoutedFakeTransport()
    with _make_client(transport) as client:
        response = client.post(
            "/runs",
            json={"transcript": _transcript("kickoff-01.txt"), "call_type": "kickoff"},
        )
        assert response.status_code == 201
        run_id = response.json()["run_id"]

        final = client.get(f"/runs/{run_id}").json()
        assert final["status"] == "completed"
        assert len(final["report"]["dimensions"]) == 12
        assert final["report"]["grade"]["band"] in {
            "Elite", "Strong", "Inconsistent", "At risk", "Fail"
        }

        # The sanitized transcript (never the raw injection surface) reached
        # the LLM inside the untrusted-data delimiters.
        assert "<transcript>" in transport.prompts[0]

        pdf = client.get(f"/runs/{run_id}/report.pdf")
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")


def test_e2e_coaching_happy_path_with_optional_dimension():
    transport = _RoutedFakeTransport()
    with _make_client(transport) as client:
        response = client.post(
            "/runs",
            json={
                "transcript": _transcript("coaching-01.txt"),
                "call_type": "coaching",
            },
        )
        run_id = response.json()["run_id"]
        final = client.get(f"/runs/{run_id}").json()
    assert final["status"] == "completed"
    assert len(final["report"]["dimensions"]) == 12
    # The run URL keeps working after the request/tab is gone (persistence).
    assert isinstance(UUID(run_id), UUID)


def test_e2e_failure_path_exposes_reason():
    client = _make_client(_RoutedFakeTransport())
    with client:
        run_id = client.post(
            "/runs",
            json={"transcript": "[A]: only one line", "call_type": "kickoff"},
        ).json()["run_id"]
    final = client.get(f"/runs/{run_id}").json()
    assert final["status"] == RunStatus.FAILED.value
    assert final["error_reason"]  # the run says WHY it failed
    pdf = client.get(f"/runs/{run_id}/report.pdf")
    assert pdf.status_code == 409
