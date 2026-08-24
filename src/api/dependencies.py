"""Dependency providers for the FastAPI application.

The app is built by `create_app(repo, llm)`; these providers make the
repository and LLM client reachable from the routes via FastAPI's DI, with
the instances fixed at factory time (tests override nothing globally).
"""

from collections.abc import Callable

from fastapi import Request

from src.agent.nodes import ScoringFn
from src.database.repository import RunRepository
from src.llm_client import GroqClient


def _getter(name: str) -> Callable:
    """Build a zero-arg provider that pulls an app-scoped instance."""

    def provider(request: Request):
        instance = getattr(request.app.state, name, None)
        if instance is None:
            raise RuntimeError(f"app.state.{name} was not configured")
        return instance

    provider.__name__ = f"get_{name}"
    provider.__doc__ = f"Provide app.state.{name}."
    return provider


get_repo = _getter("repo")  # -> RunRepository
get_llm = _getter("llm")  # -> GroqClient
get_scoring_fn = _getter("scoring_fn")  # -> ScoringFn


def set_app_state(app, repo: RunRepository, llm: GroqClient, scoring_fn: ScoringFn) -> None:
    """Attach the injected instances to the app state."""
    app.state.repo = repo
    app.state.llm = llm
    app.state.scoring_fn = scoring_fn


__all__ = ["get_llm", "get_repo", "get_scoring_fn", "set_app_state"]
