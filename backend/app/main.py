"""
FastAPI application entry point.

Startup sequence
----------------
1. lifespan context manager loads SmallCNN once.
2. CORS middleware is configured from settings.ALLOWED_ORIGINS.
3. Routers are registered with their prefixes.

The application does NOT perform any inference at startup.
The Gemini client is initialised lazily on first use.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.cnn_service import cnn_service
from app.api.routes import health as health_router
from app.api.routes import chat as chat_router
from app.api.routes import validate_mri as validate_mri_router
from app.api.routes import analyze as analyze_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — model loaded once on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load the CNN model before the server begins accepting requests."""
    logger.info("Starting up — loading CNN model...")
    try:
        cnn_service.load()
        logger.info("CNN model ready.")
    except FileNotFoundError as exc:
        # Log clearly but allow the app to start so /health can report the problem
        logger.error("CNN model checkpoint not found: %s", exc)
    except Exception as exc:
        logger.error("Failed to load CNN model: %s", exc)

    yield  # Application runs here

    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    logger.error("FileNotFoundError: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "A required resource file could not be found on the server."},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.error("RuntimeError: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "The model service is unavailable. Please try again later."},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("ValueError: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router.router)
app.include_router(chat_router.router)
app.include_router(validate_mri_router.router)
app.include_router(analyze_router.router)
