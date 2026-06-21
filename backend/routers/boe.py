"""v3 "best of both" analysis API.

    POST /api/v3/analyze   — run the pipeline; returns the report + FULL diagnostics
    GET  /api/v3/sample    — a fully-populated example run (no tokens spent)

The analyze endpoint is passphrase-gated (it spends tokens); the sample is
public so the diagnostics screen renders out of the box.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from schemas.analysis import ExtractedArticle
from schemas.boe import AnalyzeResult
from security import require_app_password
from services.article_service import ArticleService
from services.boe_sample import build_sample
from services.boe_service import BestOfBothService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3", tags=["v3"])


class V3Request(BaseModel):
    """Supply exactly one of `url` or `text`."""

    url: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "V3Request":
        has_url = bool(self.url and self.url.strip())
        has_text = bool(self.text and self.text.strip())
        if has_url == has_text:
            raise ValueError("Provide exactly one of `url` or `text`.")
        return self


async def _ingest(request: V3Request) -> ExtractedArticle:
    svc = ArticleService()
    if request.url and request.url.strip():
        return await svc.from_url(request.url.strip())
    return svc.from_text(request.text or "", title=request.title)


@router.get("/sample", response_model=AnalyzeResult)
async def sample() -> AnalyzeResult:
    """An example run with complete diagnostics — for demoing the screen."""
    return build_sample()


@router.post("/analyze", response_model=AnalyzeResult, dependencies=[Depends(require_app_password)])
async def analyze(request: V3Request) -> AnalyzeResult:
    """Run the v3 pipeline and return the report plus the full diagnostics trace."""
    logger.info(f"v3 analyze - url={bool(request.url)} text={bool(request.text)}")
    try:
        article = await _ingest(request)
        result = await BestOfBothService().analyze(article)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"v3 analyze validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"v3 analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
