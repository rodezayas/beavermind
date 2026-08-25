"""HTTP client used by the dashboard to talk to the scoring API.

The view layer never touches HTTP directly: every call goes through
`ScoringApiClient`, which maps responses and failures into plain Python
values or a single typed error carrying a human-readable `reason` (R7, R8).
This keeps the UI logic testable without a live server.
"""

from uuid import UUID

import httpx
from pydantic import ValidationError

from src.api.schemas import CreateRunRequest, CreateRunResponse, RunResponse
from src.schemas import CallType

#: Default timeout for polling/status calls (GET /runs, PDF download): these
#: never wait on the LLM itself.
DEFAULT_TIMEOUT_SECONDS = 10.0

#: Timeout for POST /runs: with SCORING_MODE=sync that request scores inline
#: and only returns once the LLM finished, so it needs to outlast the whole
#: scoring pipeline. With the default background mode the POST returns fast.
CREATE_RUN_TIMEOUT_SECONDS = 90.0


class ApiClientError(RuntimeError):
    """A failed API interaction, carrying the reason returned by the API."""

    def __init__(self, reason: str, status_code: int | None = None) -> None:
        super().__init__(reason)
        self.reason = reason  # human-readable cause, safe to show in the UI
        self.status_code = status_code  # HTTP status when the API answered


class ScoringApiClient:
    """Thin wrapper over the scoring REST API used by the dashboard."""

    def __init__(
        self,
        base_url: str,
        client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Create a client bound to the API base URL.

        Args:
            base_url: e.g. "http://localhost:8000" (no trailing slash needed).
            client: Optional pre-built httpx.Client; tests inject one backed
                by `httpx.MockTransport`. When omitted a real client is built.
            timeout: Per-request timeout in seconds.
        """
        self._client = client or httpx.Client(timeout=timeout)  # injected in tests
        self._base_url = base_url.rstrip("/")

    def create_run(self, transcript: str, call_type: CallType) -> CreateRunResponse:
        """POST /runs and return run id + URL + initial status (R1, R2).

        Raises:
            ApiClientError: On validation failure (422) or any other API /
                transport error; `reason` always carries a displayable message.
        """
        payload: CreateRunRequest
        try:
            payload = CreateRunRequest(transcript=transcript, call_type=call_type)
        except ValidationError as exc:
            # Same contract as a 422 from the server: the UI shows one reason
            raise ApiClientError(f"invalid run request: {exc}") from exc
        data = self._request_json(
            "POST",
            "/runs",
            json=payload.model_dump(mode="json"),
            expected=(201,),
            timeout=CREATE_RUN_TIMEOUT_SECONDS,  # sync scoring waits on the LLM
        )
        return CreateRunResponse.model_validate(data)

    def get_run(self, run_id: str | UUID) -> RunResponse:
        """GET /runs/{id}: status plus report or failure reason (R3, R4, R6).

        Raises:
            ApiClientError: If the run does not exist (404) or the API fails.
        """
        data = self._request_json("GET", f"/runs/{run_id}", expected=(200,))
        return RunResponse.model_validate(data)

    def download_pdf(self, run_id: str | UUID) -> bytes:
        """GET /runs/{id}/report.pdf and return the raw PDF bytes (R5).

        Raises:
            ApiClientError: If the run is not completed yet (409) or the API
                fails; `reason` explains why the PDF is not available.
        """
        try:
            response = self._client.get(f"{self._base_url}/runs/{run_id}/report.pdf")
        except httpx.HTTPError as exc:
            raise ApiClientError(f"could not reach the API: {exc}") from exc
        if response.status_code != 200:
            raise ApiClientError(
                _reason_from(response), status_code=response.status_code
            )
        return response.content

    def _request_json(
        self, method: str, path: str, *, expected: tuple[int, ...], **kwargs: object
    ) -> dict:
        """Perform a request and return the parsed JSON body.

        Centralizes error mapping so both happy paths and failures surface a
        single `ApiClientError` with the API-provided reason (R7).
        """
        try:
            response = self._client.request(method, f"{self._base_url}{path}", **kwargs)
        except httpx.HTTPError as exc:
            raise ApiClientError(f"could not reach the API: {exc}") from exc
        if response.status_code not in expected:
            raise ApiClientError(_reason_from(response), status_code=response.status_code)
        return response.json()


def _reason_from(response: httpx.Response) -> str:
    """Extract a displayable reason from an error response (R7).

    Prefers the API's structured `detail`; falls back to the raw body so a
    failure is never silent or generic.
    """
    try:
        body = response.json()
    except ValueError:
        return f"API error {response.status_code}: {response.text[:500]}"
    detail = body.get("detail") if isinstance(body, dict) else None
    if detail is None:
        return f"API error {response.status_code}: {body}"
    if isinstance(detail, list):  # FastAPI 422 validation payloads
        parts = []
        for item in detail:
            loc = ".".join(str(part) for part in item.get("loc", []) if part != "body")
            parts.append(f"{loc or 'request'}: {item.get('msg', 'invalid value')}")
        return "; ".join(parts)
    return str(detail)


__all__ = ["ApiClientError", "ScoringApiClient"]
