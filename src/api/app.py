"""FastAPI application factory.

`create_app` is the only way the API is built: repository, LLM client and
scoring function are injected, which keeps tests free of globals and
monkeypatching.
"""

from fastapi import FastAPI

from src.agent.nodes import ScoringFn
from src.api.dependencies import set_app_state
from src.api.routes import router
from src.database.repository import RunRepository
from src.llm_client import GroqClient


def create_app(
    repo: RunRepository, llm: GroqClient, scoring_fn: ScoringFn
) -> FastAPI:
    """Build the FastAPI app with its collaborators injected.

    Args:
        repo: Run storage backend (protocol `RunRepository`).
        llm: Groq client used by the scoring pipeline.
        scoring_fn: Scoring function per rubric branch (feature 5).

    Returns:
        A configured `FastAPI` application.
    """
    app = FastAPI(
        title="Scoring System",
        description="Scores call transcripts against the kick-off/coaching rubrics.",
        version="0.1.0",
    )
    set_app_state(app, repo=repo, llm=llm, scoring_fn=scoring_fn)
    app.include_router(router)
    return app


__all__ = ["create_app"]
