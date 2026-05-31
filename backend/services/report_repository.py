"""Data access for reports + visits (MariaDB via async SQLAlchemy).

Each function manages its own session so callers (the orchestrator, routers,
the tracking endpoint) don't have to. Saves/lookups are best-effort at the call
sites — a DB hiccup must never break an analysis.
"""

import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from config.settings import settings
from database import AsyncSessionLocal
from models import Report, Visit
from schemas.analysis import FairnessReport

logger = logging.getLogger(__name__)


def is_enabled() -> bool:
    """Whether report persistence/listing is available (DB configured)."""
    return settings.DB_CONFIGURED


def _summary(r: Report) -> dict:
    return {
        "report_id": r.id,
        "title": r.title,
        "topic": r.topic,
        "overall_score": r.overall_score,
        "fairness_label": r.fairness_label,
        "political_lean": r.political_lean,
        "created_at": r.created_at.replace(tzinfo=timezone.utc).isoformat()
        if r.created_at
        else None,
    }


async def save_report(report: FairnessReport, content_hash: str, source_url: Optional[str]) -> str:
    """Persist a completed v2 report; stamp report_id/created_at onto it; return id.
    The metadata columns power the Recent feed; the full report is in `payload`.
    (presentation/substantive columns are reused for the coherence/correspondence axes.)"""
    rid = secrets.token_urlsafe(9)
    now = datetime.now(timezone.utc)
    report.report_id = rid
    report.created_at = now.isoformat()

    v = report.verdict
    async with AsyncSessionLocal() as s:
        s.add(
            Report(
                id=rid,
                created_at=now.replace(tzinfo=None),
                content_hash=content_hash,
                source_url=(source_url or None),
                title=(report.article.title or "")[:512],
                topic=(report.argument.topic or "")[:512],
                overall_score=v.overall_score,
                presentation_score=v.coherence_score,
                substantive_score=v.correspondence_score,
                fairness_label=v.fairness_label,
                political_lean=v.political_lean,
                payload=report.model_dump_json(),
            )
        )
        await s.commit()
    return rid


async def get_report(report_id: str, *, count_view: bool = True) -> Optional[dict]:
    """Return the full report JSON (dict), or None. Optionally bump view_count."""
    async with AsyncSessionLocal() as s:
        row = await s.get(Report, report_id)
        if row is None:
            return None
        if count_view:
            row.view_count = (row.view_count or 0) + 1
            await s.commit()
        return json.loads(row.payload)


async def list_recent(limit: int = 24) -> list[dict]:
    async with AsyncSessionLocal() as s:
        res = await s.execute(select(Report).order_by(Report.created_at.desc()).limit(limit))
        return [_summary(r) for r in res.scalars().all()]


async def find_by_content_hash(content_hash: str) -> Optional[dict]:
    """Most recent existing report for this URL/text, or None (dedup lookup)."""
    async with AsyncSessionLocal() as s:
        res = await s.execute(
            select(Report)
            .where(Report.content_hash == content_hash)
            .order_by(Report.created_at.desc())
            .limit(1)
        )
        r = res.scalar_one_or_none()
        return _summary(r) if r else None


async def log_visit(
    *,
    ip: Optional[str],
    path: Optional[str],
    report_id: Optional[str] = None,
    referrer: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    async with AsyncSessionLocal() as s:
        s.add(
            Visit(
                ts=datetime.now(timezone.utc).replace(tzinfo=None),
                ip=(ip or None),
                path=(path or "")[:512] or None,
                report_id=report_id,
                referrer=(referrer or "")[:1024] or None,
                user_agent=(user_agent or "")[:512] or None,
            )
        )
        await s.commit()
