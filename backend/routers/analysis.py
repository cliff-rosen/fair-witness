"""Analysis API layer.

Endpoints are thin: they validate input, ask ArticleService to ingest, then
delegate to AnalysisService. Business logic lives in the services.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sse_starlette.sse import EventSourceResponse

from schemas.analysis import ExtractedArticle, FairnessReport
from security import require_app_password
from services import report_repository
from services.article_service import ArticleService
from services.content_id import compute_content_hash
from services.fairness_service import FairnessService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# --- Router-specific request schema ---

class AnalyzeRequest(BaseModel):
    """Supply exactly one of `url` or `text`.

    For pasted text, the optional provenance fields let the submitter attach the
    original source (e.g. a paywalled/blocked URL) and a note. These are display
    + dedup only — they are NOT fed into the bias analysis (which stays blind to
    source so the verdict is judged on the text alone).
    """

    url: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    source_url: Optional[str] = None  # original link for pasted text
    site_name: Optional[str] = None   # publication
    byline: Optional[str] = None      # author
    published: Optional[str] = None   # date
    note: Optional[str] = None        # submitter comment / context

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "AnalyzeRequest":
        has_url = bool(self.url and self.url.strip())
        has_text = bool(self.text and self.text.strip())
        if has_url == has_text:
            raise ValueError("Provide exactly one of `url` or `text`.")
        return self

    def effective_source_url(self) -> Optional[str]:
        """The URL we fetched, or the one the submitter attached to pasted text."""
        return (self.url or self.source_url) or None


async def _ingest(request: AnalyzeRequest) -> ExtractedArticle:
    article_service = ArticleService()
    if request.url and request.url.strip():
        article = await article_service.from_url(request.url.strip())
    else:
        article = article_service.from_text(request.text or "", title=request.title)
    # Apply submitter-provided provenance (overrides where given). Mainly used for
    # pasted text, but harmless on URL mode (fields are usually blank there).
    for field in ("source_url", "site_name", "byline", "published", "note"):
        value = getattr(request, field)
        if value and value.strip():
            setattr(article, field, value.strip())
    return article


def _content_hash(request: AnalyzeRequest) -> str:
    return compute_content_hash(url=request.effective_source_url(), text=request.text)


class PrecheckResult(BaseModel):
    """Whether this URL/text was already analyzed (so the UI can offer it)."""

    existing: Optional[dict] = None


@router.post("/precheck", response_model=PrecheckResult)
async def precheck(request: AnalyzeRequest) -> PrecheckResult:
    """Cheap dedup lookup before spending tokens. Public (no passphrase) — it
    only reads already-public report metadata. Returns the most recent existing
    report for the same URL/text, if any."""
    if not report_repository.is_enabled():
        return PrecheckResult(existing=None)
    try:
        existing = await report_repository.find_by_content_hash(_content_hash(request))
    except Exception as e:
        logger.warning(f"precheck lookup failed (continuing): {e}")
        existing = None
    return PrecheckResult(existing=existing)


@router.post("/analyze", response_model=FairnessReport, dependencies=[Depends(require_app_password)])
async def analyze(request: AnalyzeRequest) -> FairnessReport:
    """Blocking analysis: returns the full FairnessReport when finished."""
    logger.info(f"analyze called - url={bool(request.url)} text={bool(request.text)}")
    try:
        article = await _ingest(request)
        service = FairnessService()
        report = await service.analyze(article, _content_hash(request), request.effective_source_url())
        logger.info(f"analyze complete - overall={report.verdict.overall_score}")
        return report
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"analyze validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream", dependencies=[Depends(require_app_password)])
async def analyze_stream(request: AnalyzeRequest):
    """Streaming analysis: emits SSE events as each orchestration stage lands."""
    logger.info(f"analyze_stream called - url={bool(request.url)} text={bool(request.text)}")

    try:
        article = await _ingest(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = FairnessService()
    content_hash = _content_hash(request)
    source_url = request.effective_source_url()

    async def event_generator():
        async for event in service.analyze_stream(article, content_hash, source_url):
            yield {"event": event.type, "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())
