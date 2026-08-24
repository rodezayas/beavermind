"""Production entrypoint for the scoring API.

Assembles the real collaborators (Supabase repository, Groq client, rubric
scoring function) from the environment via `src.config.get_settings` and
serves the FastAPI app with uvicorn.

Usage:
    uv run python -m src.api.server            # uses SCORING_API_HOST/PORT
    # or: uv run uvicorn src.api.server:app --port 8000
"""

import os

import uvicorn
from supabase import create_client

from src.agent.nodes import ScoringFn
from src.api.app import create_app
from src.config import get_settings, load_env_file
from src.database.repository import SupabaseRunRepository
from src.llm_client import make_llm_client
from src.rubrics import load_rubric
from src.scoring import build_prompt, build_report

#: Defaults so `uv run python -m src.api.server` works out of the box
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def make_scoring_fn(llm) -> ScoringFn:
    """Build the real scoring pipeline used by both rubric branches.

    The returned callable loads the rubric for the call type, prompts the
    configured LLM provider with it, and validates the output into a `Report`.
    """
    def scoring_fn(call_type, transcript):
        """Score one transcript against its rubric end to end."""
        rubric = load_rubric(call_type)
        output = llm.complete_json(build_prompt(call_type, transcript, rubric))
        return build_report(output, rubric)

    return scoring_fn


def build_production_app():
    """Assemble the API with real Supabase + the configured LLM provider.

    Raises:
        ConfigError: If any mandatory environment variable is missing.
    """
    load_env_file()  # local development: read .env; real env vars take precedence
    settings = get_settings()  # fails fast with the missing variable names
    supabase_url = f"https://{settings.supabase_project_id}.supabase.co"
    # The service-role key (SUPABASE_SECRET_KEY) is required for server writes
    client = create_client(supabase_url, settings.supabase_secret_key)
    llm = make_llm_client(settings)  # provider chosen by LLM_PROVIDER
    return create_app(
        repo=SupabaseRunRepository(client),
        llm=llm,
        scoring_fn=make_scoring_fn(llm),
    )


# Module-level app so `uvicorn src.api.server:app` works too
app = build_production_app()

if __name__ == "__main__":
    host = os.environ.get("SCORING_API_HOST", DEFAULT_HOST)
    port = int(os.environ.get("SCORING_API_PORT", str(DEFAULT_PORT)))
    uvicorn.run(app, host=host, port=port)
