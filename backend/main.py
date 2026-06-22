from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from config import setup_logging, settings
from routers import admin, analysis, analyze, reports

logger = setup_logging()
logger.info(f"{settings.APP_NAME} v{settings.SETTING_VERSION} starting")

app = FastAPI(title=settings.APP_NAME, version=settings.SETTING_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(analyze.router)


@app.on_event("startup")
async def _startup() -> None:
    """Create DB tables if configured. Best-effort: a DB problem shouldn't stop
    the app from serving health/analysis — persistence just degrades."""
    if not settings.DB_CONFIGURED:
        logger.warning("DB not configured — reports/recent/tracking disabled")
        return
    try:
        from database import init_db

        await init_db()
    except Exception as e:
        logger.error(f"DB init failed (persistence disabled this run): {e}")


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} API", "docs": "/docs", "health": "/api/health"}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.SETTING_VERSION,
        "anthropic_key_configured": bool(settings.ANTHROPIC_API_KEY),
        "model": settings.CLAUDE_MODEL,
    }


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"RequestValidationError in {request.url.path}: {exc.errors()}")
    # jsonable_encoder: Pydantic v2 puts a raw ValueError in errors()[..]['ctx'],
    # which json.dumps can't serialize — without this the 422 crashes into a 500.
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception in {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {type(exc).__name__}"}
    )
