"""Run repository: protocol plus Supabase and in-memory implementations.

The rest of the system depends only on the `RunRepository` protocol; storage
is a swappable detail. `SupabaseRunRepository` is the production backend (the
`runs` table is the single source of truth, so run URLs keep working across
sessions); `InMemoryRunRepository` backs tests and local development.
"""

from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from src.schemas import Run

#: Table name in the Supabase schema (see schema.sql)
RUNS_TABLE = "runs"


class RepositoryError(RuntimeError):
    """Raised when a storage operation fails; carries run id and cause."""

    def __init__(
        self,
        message: str,
        run_id: UUID | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.run_id = run_id
        self.cause = cause


def _utcnow() -> datetime:
    """Current UTC time (used to refresh `updated_at` on writes)."""
    return datetime.now(timezone.utc)


def _to_row(run: Run) -> dict:
    """Serialize a Run to the storage row shape."""
    return run.model_dump(mode="json")


def _from_row(row: dict) -> Run:
    """Deserialize a storage row back into a Run."""
    return Run.model_validate(row)


class RunRepository(Protocol):
    """Storage contract for scoring runs."""

    def create(self, run: Run) -> Run:
        """Persist a new run and return it unchanged."""
        ...  # pragma: no cover

    def get(self, run_id: UUID) -> Run | None:
        """Return the stored run, or None when the id does not exist."""
        ...  # pragma: no cover

    def update(self, run: Run) -> Run:
        """Persist status/report/error changes and refresh `updated_at`."""
        ...  # pragma: no cover


class InMemoryRunRepository:
    """Dict-backed repository for tests and local development."""

    def __init__(self) -> None:
        """Start with empty storage."""
        self._runs: dict[UUID, Run] = {}

    def create(self, run: Run) -> Run:
        """Persist a new run; duplicates are a repository error."""
        if run.run_id in self._runs:
            raise RepositoryError(
                f"run {run.run_id} already exists", run_id=run.run_id
            )
        stored = run.model_copy()
        self._runs[run.run_id] = stored
        return stored

    def get(self, run_id: UUID) -> Run | None:
        """Return a copy of the stored run, or None when missing."""
        run = self._runs.get(run_id)
        return run.model_copy() if run is not None else None

    def update(self, run: Run) -> Run:
        """Persist changes over an existing run, refreshing `updated_at`."""
        if run.run_id not in self._runs:
            raise RepositoryError(
                f"cannot update missing run {run.run_id}", run_id=run.run_id
            )
        stored = run.model_copy(update={"updated_at": _utcnow()})
        self._runs[run.run_id] = stored
        return stored


class SupabaseRunRepository:
    """Production repository backed by the Supabase `runs` table."""

    def __init__(self, client) -> None:
        """Create the repository.

        Args:
            client: A Supabase client (anything exposing `.table(name)`), so
                tests can inject a fake without network access.
        """
        self._client = client

    def create(self, run: Run) -> Run:
        """Insert the run row; constraint or connection errors are wrapped."""
        try:
            self._client.table(RUNS_TABLE).insert(_to_row(run)).execute()
        except Exception as exc:
            raise RepositoryError(
                f"failed to create run {run.run_id}: {exc}",
                run_id=run.run_id,
                cause=exc,
            ) from exc
        return run

    def get(self, run_id: UUID) -> Run | None:
        """Fetch the run row by id; missing ids return None (never raise)."""
        try:
            response = (
                self._client.table(RUNS_TABLE)
                .select("*")
                .eq("run_id", str(run_id))
                .execute()
            )
        except Exception as exc:
            raise RepositoryError(
                f"failed to fetch run {run_id}: {exc}", run_id=run_id, cause=exc
            ) from exc
        rows = getattr(response, "data", None) or []
        if not rows:
            return None
        return _from_row(rows[0])

    def update(self, run: Run) -> Run:
        """Update the run row, refreshing `updated_at` server-side and locally."""
        row = _to_row(run.model_copy(update={"updated_at": _utcnow()}))
        try:
            (
                self._client.table(RUNS_TABLE)
                .update(row)
                .eq("run_id", str(run.run_id))
                .execute()
            )
        except Exception as exc:
            raise RepositoryError(
                f"failed to update run {run.run_id}: {exc}",
                run_id=run.run_id,
                cause=exc,
            ) from exc
        return run.model_copy(update={"updated_at": row["updated_at"]})


__all__ = [
    "RUNS_TABLE",
    "InMemoryRunRepository",
    "RepositoryError",
    "RunRepository",
    "SupabaseRunRepository",
]
