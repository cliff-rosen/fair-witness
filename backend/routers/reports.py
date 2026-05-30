"""Public report-viewing + Recent feed + visit tracking.

All endpoints here are public (no passphrase). Reports are created server-side
by the analysis orchestrator; there is no public write path for them.
"""

import logging
import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services import report_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reports"])

# Share ids are token_urlsafe (URL-safe base64).
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _client_ip(request: Request) -> str | None:
    """Real client IP — behind the EB ALB the address is in X-Forwarded-For."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("/reports")
async def list_recent(limit: int = 24):
    """Newest-first report summaries for the Recent feed."""
    limit = max(1, min(limit, 100))
    if not report_repository.is_enabled():
        return []
    try:
        return await report_repository.list_recent(limit)
    except Exception as e:
        logger.error(f"list_recent failed: {e}", exc_info=True)
        return []


@router.get("/reports/{report_id}")
async def get_report(report_id: str, request: Request):
    if not _ID_RE.match(report_id):
        raise HTTPException(status_code=404, detail="Report not found.")
    if not report_repository.is_enabled():
        raise HTTPException(status_code=404, detail="Report sharing is not configured.")
    try:
        data = await report_repository.get_report(report_id)
    except Exception as e:
        logger.error(f"Failed to fetch report {report_id}: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Could not load report.")
    if data is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    # Best-effort: record that this report was opened (counts toward tracking).
    try:
        await report_repository.log_visit(
            ip=_client_ip(request),
            path=f"/r/{report_id}",
            report_id=report_id,
            referrer=request.headers.get("referer"),
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        pass
    return data


class TrackEvent(BaseModel):
    path: str
    referrer: str | None = None


@router.post("/track", status_code=204)
async def track(event: TrackEvent, request: Request):
    """Lightweight page-view beacon from the frontend. Records IP + what they
    viewed. Best-effort: never fails the caller."""
    if report_repository.is_enabled():
        try:
            await report_repository.log_visit(
                ip=_client_ip(request),
                path=event.path,
                referrer=event.referrer or request.headers.get("referer"),
                user_agent=request.headers.get("user-agent"),
            )
        except Exception as e:
            logger.debug(f"track failed (ignored): {e}")
    return None
