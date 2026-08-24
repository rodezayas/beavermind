"""Application configuration loaded from environment variables.

`Settings` centralizes every external credential/endpoint the scoring system
needs. Missing mandatory variables fail fast with an explicit error.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class ConfigError(RuntimeError):
    """Raised when mandatory configuration is missing or invalid."""


#: Environment variables that must be present regardless of LLM provider
MANDATORY_ENV_VARS: tuple[str, ...] = (
    "SUPABASE_PROJECT_ID",
    "SUPABASE_API_KEY",
    "SUPABASE_SECRET_KEY",
)

#: API key variable required per LLM provider (env LLM_PROVIDER)
PROVIDER_KEY_VAR: dict[str, str] = {
    "groq": "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


class Settings(BaseModel):
    """Immutable snapshot of the environment configuration."""

    supabase_project_id: str
    supabase_api_key: str
    supabase_secret_key: str
    groq_api_key: str
    database: str
    rubrics_dir: str = "rubrics"  # overridable for tests
    groq_model: str = "groq/compound-mini"  # 70k TPM free tier; see README
    llm_provider: str = "groq"  # "groq" | "anthropic" (env LLM_PROVIDER)
    anthropic_api_key: str = ""  # required when llm_provider == "anthropic"
    anthropic_model: str = "claude-sonnet-5"  # env ANTHROPIC_MODEL


def load_env_file(path: str | Path = ".env") -> None:
    """Load KEY=VALUE pairs from a `.env` file into `os.environ`.

    Existing environment variables always win (the file never overrides an
    explicitly exported value). Lines without `=` and comments (`#`) are
    skipped. Values may be wrapped in single or double quotes.

    Args:
        path: Dotenv file location; missing files are ignored silently so
            production deployments that configure real env vars keep working.
    """
    env_file = Path(path)
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue  # comment, blank, or malformed line
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


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
    provider = env.get("LLM_PROVIDER", "groq").strip().lower()
    if provider not in PROVIDER_KEY_VAR:
        raise ConfigError(
            f"Invalid LLM_PROVIDER {provider!r}: expected one of "
            f"{', '.join(sorted(PROVIDER_KEY_VAR))}"
        )
    missing = [name for name in MANDATORY_ENV_VARS if not env.get(name)]
    provider_key_var = PROVIDER_KEY_VAR[provider]
    if not env.get(provider_key_var):
        missing.append(provider_key_var)
    if missing:
        raise ConfigError(
            f"Missing mandatory environment variables: {', '.join(missing)}"
        )
    return Settings(
        supabase_project_id=env["SUPABASE_PROJECT_ID"],
        supabase_api_key=env["SUPABASE_API_KEY"],
        supabase_secret_key=env["SUPABASE_SECRET_KEY"],
        groq_api_key=env.get("GROQ_API_KEY", ""),
        database=env.get("DATABASE", ""),  # optional; unused by the current stack
        rubrics_dir=env.get("RUBRICS_DIR", "rubrics"),
        groq_model=env.get("GROQ_MODEL", "groq/compound-mini"),
        llm_provider=provider,
        anthropic_api_key=env.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=env.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
    )


__all__ = ["ConfigError", "Settings", "get_settings"]
