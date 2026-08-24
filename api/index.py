"""Vercel serverless entrypoint for the scoring API.

Exposes the FastAPI app assembled with real Supabase + the configured LLM
provider. Set `SCORING_MODE=sync` in the Vercel environment variables:
serverless functions freeze after the response, so background scoring
threads would never finish — the sync mode scores inline instead.
"""

from src.api.server import app

# Vercel's Python runtime looks for `app` in this module
runtime = "python3.11"  # noqa: F841 - documents the target runtime
