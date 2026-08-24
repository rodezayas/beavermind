"""Tests for the run repository (feature: database_supabase).

Runs against `InMemoryRunRepository` plus a fake Supabase client for the
error-wrapping path; no network or credentials involved.
"""

from datetime import timedelta
from uuid import uuid4

import pytest

from src.database.repository import (
    InMemoryRunRepository,
    RepositoryError,
    SupabaseRunRepository,
)
from src.schemas import CallType, Report, Run, RunStatus


def _run(**overrides) -> Run:
    defaults = dict(call_type=CallType.KICKOFF, transcript="[A]: hi\n[B]: hello")
    defaults.update(overrides)
    return Run(**defaults)


def _report() -> Report:
    from src.schemas import DimensionScore, Grade, OneThing

    return Report(
        one_thing=OneThing(change="book live", projected_score=90),
        brief="ok",
        red_flags=[],
        grade=Grade(total=80, band="Strong"),
        dimensions=[
            DimensionScore(
                dimension_id=i,
                name=f"D{i}",
                max_points=5,
                score=4,
                band="Strong",
                reasoning="r",
                quick_fix="q",
            )
            for i in range(1, 13)
        ],
    )


# --- R5 / R6: create & get ---------------------------------------------------


def test_create_returns_run():
    repo = InMemoryRunRepository()
    run = _run()
    assert repo.create(run).run_id == run.run_id


def test_get_missing_returns_none():
    assert InMemoryRunRepository().get(uuid4()) is None


# --- R2 / R4 / R9: protocol & roundtrip -------------------------------------


def test_in_memory_repository_roundtrip():
    repo = InMemoryRunRepository()
    run = repo.create(_run())
    fetched = repo.get(run.run_id)
    assert fetched == run


def test_roundtrip_preserves_all_fields():
    repo = InMemoryRunRepository()
    original = repo.create(
        _run(
            status=RunStatus.COMPLETED,
            report=_report(),
            error_reason=None,
        )
    )
    fetched = repo.get(original.run_id)
    assert fetched.status is RunStatus.COMPLETED
    assert fetched.report == original.report
    assert fetched.created_at == original.created_at
    assert fetched.transcript == original.transcript


# --- R7: update --------------------------------------------------------------


def test_update_persists_failure_with_reason():
    repo = InMemoryRunRepository()
    run = repo.create(_run())
    failed = run.model_copy(
        update={"status": RunStatus.FAILED, "error_reason": "LLM quota exceeded"}
    )
    repo.update(failed)
    assert repo.get(run.run_id).error_reason == "LLM quota exceeded"
    assert repo.get(run.run_id).status is RunStatus.FAILED


def test_update_persists_completed_report():
    repo = InMemoryRunRepository()
    run = repo.create(_run())
    done = run.model_copy(
        update={"status": RunStatus.COMPLETED, "report": _report()}
    )
    repo.update(done)
    assert repo.get(run.run_id).report is not None


def test_update_refreshes_updated_at():
    repo = InMemoryRunRepository()
    run = repo.create(_run())
    stale = run.model_copy(update={"updated_at": run.updated_at - timedelta(hours=1)})
    updated = repo.update(stale)
    assert updated.updated_at > stale.updated_at


def test_update_missing_run_raises():
    with pytest.raises(RepositoryError):
        InMemoryRunRepository().update(_run())


def test_create_duplicate_raises():
    repo = InMemoryRunRepository()
    run = repo.create(_run())
    with pytest.raises(RepositoryError):
        repo.create(run)


# --- R8: error wrapping (fake Supabase client) -------------------------------


class _ExplodingTable:
    """Fake supabase table accessor that always fails on execute()."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def insert(self, _row):
        return self

    def select(self, _cols):
        return self

    def update(self, _row):
        return self

    def eq(self, _col, _val):
        return self

    def execute(self):
        raise self._error


class _ExplodingClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def table(self, _name):
        return _ExplodingTable(self._error)


class _OkClient:
    """Fake supabase client storing rows in memory (minimal contract)."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def table(self, _name):
        client = self

        class _Query:
            def __init__(self) -> None:
                self._row = None
                self._id = None

            def insert(self, row):
                self._row = row
                return self

            def update(self, row):
                self._row = row
                return self

            def select(self, _cols):
                return self

            def eq(self, _col, val):
                self._id = val
                return self

            def execute(self):
                if self._id is not None:  # select/update path
                    if self._row is not None:  # update
                        client.rows[self._id] = self._row
                    found = client.rows.get(self._id)
                    data = [found] if found else []
                    return type("R", (), {"data": data})
                client.rows[self._row["run_id"]] = self._row
                return type("R", (), {"data": [self._row]})

        return _Query()


def test_repository_error_wraps_cause():
    cause = ConnectionError("network down")
    repo = SupabaseRunRepository(_ExplodingClient(cause))
    run = _run()
    with pytest.raises(RepositoryError) as exc:
        repo.create(run)
    assert exc.value.run_id == run.run_id
    assert exc.value.cause is cause
    assert "network down" in str(exc.value)


def test_supabase_repository_roundtrip_with_fake_client():
    repo = SupabaseRunRepository(_OkClient())
    run = repo.create(_run())
    assert repo.get(run.run_id) == run
    done = run.model_copy(
        update={"status": RunStatus.FAILED, "error_reason": "boom"}
    )
    repo.update(done)
    assert repo.get(run.run_id).error_reason == "boom"


# --- R1: schema file ---------------------------------------------------------


def test_schema_sql_defines_runs_table():
    from pathlib import Path

    ddl = Path("src/database/schema.sql").read_text()
    assert "create table if not exists beaverops" in ddl
    for column in ("run_id", "call_type", "status", "transcript", "report",
                   "error_reason", "created_at", "updatet_at"):
        assert column in ddl


# --- storage row mapping (live table uses `updatet_at`) -----------------------


def test_row_mapping_renames_updated_at_column():
    """Rows use the live column name `updatet_at`; domain keeps `updated_at`."""
    from src.database.repository import UPDATED_AT_COLUMN, _to_row, _from_row

    run = _run()
    row = _to_row(run)
    assert "updated_at" not in row  # domain name never leaks to storage
    assert UPDATED_AT_COLUMN in row
    restored = _from_row(row)
    assert restored == run
