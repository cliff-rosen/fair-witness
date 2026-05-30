"""Application settings.

Mirrors the TableThat / aftershoot settings pattern (pydantic-settings + dotenv).
Environment is selected before any dotenv load:

    ENVIRONMENT=production  ->  load .env.production  (set this on Elastic Beanstalk)
    ENVIRONMENT unset       ->  load .env            (local dev — safe default)
"""

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_backend_dir = Path(__file__).resolve().parent.parent
_is_production = os.getenv("ENVIRONMENT") == "production"
_env_file = ".env.production" if _is_production else ".env"
load_dotenv(_backend_dir / _env_file, override=True)


def _get_git_version() -> str:
    """Resolve the build version: BUILD_VERSION file -> git tag -> short SHA."""
    # 1. BUILD_VERSION file (written by deploy.ps1, shipped in the EB bundle).
    version_file = _backend_dir / "BUILD_VERSION"
    if version_file.exists():
        v = version_file.read_text().strip()
        if v:
            return v
    # 2. Latest git tag (e.g. "v1.0.3").
    for args in (["git", "describe", "--tags", "--abbrev=0"], ["git", "rev-parse", "--short", "HEAD"]):
        try:
            out = subprocess.check_output(
                args, stderr=subprocess.DEVNULL, cwd=str(_backend_dir), timeout=5
            ).decode().strip()
            if out:
                return out
        except Exception:
            pass
    # 3. Fallback.
    return "0.1.0"


# Frontend origin — used for CORS in production. Overridable via env.
_frontend_url = os.getenv("FRONTEND_URL", "https://fairwitness.orchestratorstudios.ai")


class Settings(BaseSettings):
    APP_NAME: str = "Fair Witness"
    SETTING_VERSION: str = _get_git_version()
    IS_PRODUCTION: bool = _is_production
    FRONTEND_URL: str = _frontend_url

    # --- Anthropic ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Model used by every prompt caller unless overridden per-caller.
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # --- Orchestration knobs ---
    # Cap on concurrent dimension evaluators in the fan-out stage.
    MAX_PARALLEL_EVALUATORS: int = int(os.getenv("MAX_PARALLEL_EVALUATORS", "8"))
    # Truncate very long articles before sending to the model (characters).
    MAX_ARTICLE_CHARS: int = int(os.getenv("MAX_ARTICLE_CHARS", "40000"))
    # Reader-service fallback for URLs that block a direct fetch (JS-heavy /
    # Cloudflare / paywalled). Empty string disables the fallback.
    READER_FALLBACK_URL: str = os.getenv("READER_FALLBACK_URL", "https://r.jina.ai/")

    # --- Access gate (Phase 2) ---
    # Single shared passphrase required to GENERATE an analysis. Empty = open
    # (dev mode). Viewing a shared report never requires this.
    APP_PASSWORD: str = os.getenv("APP_PASSWORD", "")
    # SEPARATE secret for the /admin tracking dashboard (don't reuse APP_PASSWORD,
    # which is circulated widely). Empty = admin API disabled.
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")

    # --- Database (shared MariaDB `chatter` on RDS; new `fairwitness` schema) ---
    # Mirrors the TableThat / aftershoot pattern (SQLAlchemy + PyMySQL/aiomysql).
    # Local dev points at the same cloud instance.
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "fairwitness")

    # --- CORS ---
    # Lock to the real frontend in prod; wide-open for local dev. The passphrase
    # travels as a header (not a cookie), so credentials are not needed — which
    # also keeps the wildcard dev origin valid.
    CORS_ORIGINS: list[str] = [_frontend_url] if _is_production else ["*"]
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DB_CONFIGURED(self) -> bool:
        return bool(self.DB_HOST and self.DB_USER and self.DB_NAME)

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
