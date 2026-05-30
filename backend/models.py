"""ORM models for the consolidated MariaDB datastore.

Two tables:
  • reports — the full BiasReport JSON (payload) + indexed metadata columns that
    power the Recent feed, dedup (content_hash), and future "top" rankings.
  • visits  — one row per tracked page view / report open: IP, path, referrer.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

# Full report JSON can exceed TEXT's 64KB on MySQL → LONGTEXT there, plain TEXT
# elsewhere (e.g. SQLite in tests).
_JSON = Text().with_variant(LONGTEXT, "mysql")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(24), primary_key=True)  # token_urlsafe share id
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    # sha256 of the normalized URL or text — used to detect "already analyzed".
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    title: Mapped[str] = mapped_column(String(512), default="")
    topic: Mapped[str] = mapped_column(String(512), default="")
    overall_score: Mapped[int] = mapped_column(Integer, default=0)
    presentation_score: Mapped[int] = mapped_column(Integer, default=0)
    substantive_score: Mapped[int] = mapped_column(Integer, default=0)
    fairness_label: Mapped[str] = mapped_column(String(32), default="")
    political_lean: Mapped[str] = mapped_column(String(32), default="")
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    payload: Mapped[str] = mapped_column(_JSON)  # the full BiasReport JSON


class Visit(Base):
    __tablename__ = "visits"

    # BIGINT on MySQL; SQLite only autoincrements INTEGER PRIMARY KEY, so vary it.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    report_id: Mapped[Optional[str]] = mapped_column(String(24), nullable=True, index=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
