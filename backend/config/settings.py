"""Application settings.

Mirrors the TableThat settings pattern (pydantic-settings + dotenv) but pared
down for the Fair Witness proof of concept: no database, no auth — just the
Anthropic credentials and a couple of orchestration knobs.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env", override=True)


class Settings(BaseSettings):
    APP_NAME: str = "Fair Witness"
    SETTING_VERSION: str = "0.1.0"

    # --- Anthropic ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Model used by every prompt caller unless overridden per-caller.
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # --- Orchestration knobs ---
    # Cap on concurrent dimension evaluators in the fan-out stage.
    MAX_PARALLEL_EVALUATORS: int = int(os.getenv("MAX_PARALLEL_EVALUATORS", "8"))
    # Truncate very long articles before sending to the model (characters).
    MAX_ARTICLE_CHARS: int = int(os.getenv("MAX_ARTICLE_CHARS", "40000"))

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
