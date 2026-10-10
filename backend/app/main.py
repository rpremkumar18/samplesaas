"""FastAPI application entrypoint."""

import asyncio
import contextlib
import importlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.exceptions import AppError
from app.rate_limit import limiter

settings = get_settings()
logger = logging.getLogger(__name__)

ROUTER_MODULES = ["auth", "submissions", "roasts", "admin"]
SWEEP_INTERVAL_SECONDS = 300


def configure_logging() -> None:
    """Configure root logging from settings."""
    logging.basicConfig(
        level=settings.LOG_LEVEL.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def include_routers(app: FastAPI) -> None:
    """Mount every existing router module under /api/v1."""
    for name in ROUTER_MODULES:
        module_name = f"app.routers.{name}"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name != module_name:
                raise
            logger.debug("Router %s not present yet; skipping", name)
            continue
        app.include_router(module.router, prefix="/api/v1")
        logger.info("Mounted router: %s", name)


def run_sweeper() -> int:
    """Fail stale in-flight submissions; tolerant of a missing or failing sweeper.

    The sweeper is imported lazily so the app still starts if it is unavailable.
    """
    try:
        from app.services.submission_service import sweep_stale_submissions
    except ImportError:
        logger.warning("sweep_stale_submissions is not available; skipping sweep")
        return 0
    try:
        return int(sweep_stale_submissions())
    except Exception:
        logger.exception("Stale submission sweep failed")
        return 0


async def _sweep_loop(interval: float = SWEEP_INTERVAL_SECONDS) -> None:
    """Run the sweeper at startup and then periodically until cancelled."""
    while True:
        await asyncio.to_thread(run_sweeper)
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown hook (runs the stale-submission sweeper)."""
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    task = asyncio.create_task(_sweep_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()
    is_prod = settings.ENVIRONMENT.lower() == "production"
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        """Convert domain errors into JSON responses."""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return a 422 body without echoing submitted input or raw ctx objects."""
        errors = [
            {k: v for k, v in err.items() if k not in ("input", "ctx")} for err in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
        """Log unexpected errors and hide internals from clients."""
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "healthy"}

    include_routers(app)
    return app


app = create_app()
