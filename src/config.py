"""Application configuration loaded from environment variables.

`Settings` centralizes every external credential/endpoint the scoring system
needs. Missing mandatory variables fail fast with an explicit error.
"""

import os
from functools import lru_cache

from pydantic import BaseModel


class ConfigError(RuntimeError):
    """Raised when mandatory configuration is missing or invalid."""


#: Environment variables that must be present for the system to operate
MANDATORY_ENV_VARS: tuple[str, ...] = (
    "SUPABASE_PROJECT_ID",
    "SUPABASE_API_KEY",
    "SUPABASE_SECRET_KEY",
    "GROQ_API_KEY",
    "DATABASE",
)


class Settings(BaseModel):
    """Immutable snapshot of the environment configuration."""

    supabase_project_id: str
    supabase_api_key: str
    supabase_secret_key: str
    groq_api_key: str
    database: str
    rubrics_dir: str = "rubrics"  # overridable for tests


def get_settings(environ: dict[str, str] | None = None) -> Settings:
    """Build `Settings` from the process environment (or a provided mapping).

    Args:
        environ: Mapping to read variables from; defaults to `os.environ`.
            Injected by tests to avoid touching the real environment.

    Returns:
        A validated `Settings` instance.

    Raises:
        ConfigError: If any mandatory variable is missing or empty. The
            message names every missing variable.
    """
    env = os.environ if environ is None else environ
    missing = [name for name in MANDATORY_ENV_VARS if not env.get(name)]
    if missing:
        raise ConfigError(
            f"Missing mandatory environment variables: {', '.join(missing)}"
        )
    return Settings(
        supabase_project_id=env["SUPABASE_PROJECT_ID"],
        supabase_api_key=env["SUPABASE_API_KEY"],
        supabase_secret_key=env["SUPABASE_SECRET_KEY"],
        groq_api_key=env["GROQ_API_KEY"],
        database=env["DATABASE"],
        rubrics_dir=env.get("RUBRICS_DIR", "rubrics"),
    )


__all__ = ["ConfigError", "Settings", "get_settings"]
