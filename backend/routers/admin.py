"""Admin tracking dashboard API. Gated by ADMIN_PASSWORD (X-Admin-Password
header) — separate from the analysis passphrase, and disabled if unset."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from security import require_admin
from services import admin_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/overview")
async def overview():
    try:
        return await admin_repository.overview()
    except Exception as e:
        logger.error(f"admin overview failed: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Could not load admin overview.")


@router.get("/visits")
async def visits(limit: int = 100, offset: int = 0):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    try:
        return await admin_repository.list_visits(limit, offset)
    except Exception as e:
        logger.error(f"admin visits failed: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Could not load visits.")
