"""Application settings loaded from environment variables.

Every variable uses the ``EMPORIO_`` prefix, for example::

    EMPORIO_MODEL_PROVIDER=openai
    EMPORIO_OLLAMA_MODEL=llama3.1:8b

Requires ``pydantic-settings`` (installed in Phase 0).
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Emporio da Musica agent."""

    model_config = SettingsConfigDict(env_prefix="EMPORIO_", env_file=".env", extra="ignore")

    # LLM provider selection. Ollama (local, free) is the default; switch to
    # "openai" only when a paid API key is configured.
    model_provider: Literal["ollama", "openai"] = "ollama"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    openai_api_key: str | None = Field(default=None)
    openai_model: str = "gpt-4o-mini"

    # Sampling temperature for both providers. Low default: a store agent should be
    # boring — same question, same answer — and steady sampling keeps tool-calling
    # reliable. Override per deployment with EMPORIO_TEMPERATURE.
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Local data and runtime paths.
    data_dir: str = "data"
    database_path: str = "emporio.sqlite"
    session_log_path: str = "sessions.jsonl"

    # Safety cap on consecutive tool-calling steps per user turn.
    max_tool_steps: int = 8


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
