"""Read-only aggregate queries for the /admin tracking dashboard."""

from datetime import timezone

from sqlalchemy import func, select

from database import AsyncSessionLocal
from models import Report, Visit


def _iso(dt) -> str | None:
    return dt.replace(tzinfo=timezone.utc).isoformat() if dt else None


async def overview(recent_limit: int = 50) -> dict:
    async with AsyncSessionLocal() as s:
        total_visits = (await s.execute(select(func.count()).select_from(Visit))).scalar() or 0
        unique_ips = (
            await s.execute(select(func.count(func.distinct(Visit.ip))))
        ).scalar() or 0
        total_reports = (await s.execute(select(func.count()).select_from(Report))).scalar() or 0
        report_views = (
            await s.execute(select(func.coalesce(func.sum(Report.view_count), 0)))
        ).scalar() or 0

        recent = (
            (await s.execute(select(Visit).order_by(Visit.id.desc()).limit(recent_limit)))
            .scalars()
            .all()
        )
        top_reports = (
            (await s.execute(select(Report).order_by(Report.view_count.desc()).limit(10)))
            .scalars()
            .all()
        )

        cnt = func.count(Visit.id)
        ref_rows = (
            await s.execute(
                select(Visit.referrer, cnt).group_by(Visit.referrer).order_by(cnt.desc()).limit(10)
            )
        ).all()
        path_rows = (
            await s.execute(
                select(Visit.path, cnt).group_by(Visit.path).order_by(cnt.desc()).limit(10)
            )
        ).all()
        day = func.date(Visit.ts).label("day")
        day_rows = (
            await s.execute(select(day, cnt).group_by(day).order_by(day.desc()).limit(30))
        ).all()

    return {
        "totals": {
            "visits": total_visits,
            "unique_ips": unique_ips,
            "reports": total_reports,
            "report_views": int(report_views),
        },
        "recent_visits": [
            {
                "ts": _iso(v.ts),
                "ip": v.ip,
                "path": v.path,
                "report_id": v.report_id,
                "referrer": v.referrer,
                "user_agent": v.user_agent,
            }
            for v in recent
        ],
        "top_reports": [
            {
                "report_id": r.id,
                "title": r.title,
                "view_count": r.view_count,
                "overall_score": r.overall_score,
                "fairness_label": r.fairness_label,
            }
            for r in top_reports
        ],
        "top_referrers": [
            {"referrer": (ref or "(direct)"), "count": c} for ref, c in ref_rows
        ],
        "top_paths": [{"path": (p or "(unknown)"), "count": c} for p, c in path_rows],
        "by_day": [{"day": str(d), "count": c} for d, c in day_rows],
    }


async def list_visits(limit: int = 100, offset: int = 0) -> list[dict]:
    async with AsyncSessionLocal() as s:
        rows = (
            (
                await s.execute(
                    select(Visit).order_by(Visit.id.desc()).limit(limit).offset(offset)
                )
            )
            .scalars()
            .all()
        )
    return [
        {
            "ts": _iso(v.ts),
            "ip": v.ip,
            "path": v.path,
            "report_id": v.report_id,
            "referrer": v.referrer,
            "user_agent": v.user_agent,
        }
        for v in rows
    ]
