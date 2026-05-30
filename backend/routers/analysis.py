"""Analysis API layer.

Endpoints are thin: they validate input, ask ArticleService to ingest, then
delegate to AnalysisService. Business logic lives in the services.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from sse_starlette.sse import EventSourceResponse

from schemas.analysis import BiasReport, ExtractedArticle
from services.analysis_service import AnalysisService
from services.article_service import ArticleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# --- Router-specific request schema ---

class AnalyzeRequest(BaseModel):
    """Supply exactly one of `url` or `text`."""

    url: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None  # optional title hint for pasted text

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "AnalyzeRequest":
        has_url = bool(self.url and self.url.strip())
        has_text = bool(self.text and self.text.strip())
        if has_url == has_text:
            raise ValueError("Provide exactly one of `url` or `text`.")
        return self


async def _ingest(request: AnalyzeRequest) -> ExtractedArticle:
    article_service = ArticleService()
    if request.url and request.url.strip():
        return await article_service.from_url(request.url.strip())
    return article_service.from_text(request.text or "", title=request.title)


@router.post("/analyze", response_model=BiasReport)
async def analyze(request: AnalyzeRequest) -> BiasReport:
    """Blocking analysis: returns the full BiasReport when finished."""
    logger.info(f"analyze called - url={bool(request.url)} text={bool(request.text)}")
    try:
        article = await _ingest(request)
        service = AnalysisService()
        report = await service.analyze(article)
        logger.info(f"analyze complete - score={report.overall.overall_score}")
        return report
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"analyze validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def analyze_stream(request: AnalyzeRequest):
    """Streaming analysis: emits SSE events as each orchestration stage lands."""
    logger.info(f"analyze_stream called - url={bool(request.url)} text={bool(request.text)}")

    try:
        article = await _ingest(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    service = AnalysisService()

    async def event_generator():
        async for event in service.analyze_stream(article):
            yield {"event": event.type, "data": event.model_dump_json()}

    return EventSourceResponse(event_generator())
