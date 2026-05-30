"""Shared-passphrase access gate.

A single FastAPI dependency that protects the analysis-*generating* endpoints
(`POST /api/analysis/analyze`, `POST /api/analysis/stream`). Viewing a stored
report (`GET /api/reports/{id}`) is intentionally NOT gated — anyone with a
share link can open it. The gate exists to protect Anthropic token spend.

If `APP_PASSWORD` is empty (local dev), the gate is a no-op. Mirrors aftershoot's
single-shared-password pattern, but applied per-route instead of globally so the
public report path stays open.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException

from config.settings import settings

logger = logging.getLogger(__name__)


async def require_app_password(
    x_app_password: Optional[str] = Header(default=None),
) -> None:
    if not settings.APP_PASSWORD:
        return  # open in dev / when no passphrase is configured
    if x_app_password != settings.APP_PASSWORD:
        logger.warning("Rejected analysis request: missing or invalid passphrase")
        raise HTTPException(status_code=401, detail="Invalid or missing access passphrase.")


async def require_admin(
    x_admin_password: Optional[str] = Header(default=None),
) -> None:
    """Gate the /admin tracking endpoints. If ADMIN_PASSWORD is unset the admin
    API is disabled entirely (404) rather than open."""
    if not settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=404, detail="Admin is not configured.")
    if x_admin_password != settings.ADMIN_PASSWORD:
        logger.warning("Rejected admin request: missing or invalid admin password")
        raise HTTPException(status_code=401, detail="Invalid admin password.")
