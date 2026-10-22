"""FastAPI application factory.

Creates the app with CORS, lifespan (model loading), database initialization,
and all route registrations.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on the path for ml imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.core.config import settings
from backend.app.core.errors import AppError, app_error_handler, generic_error_handler
from backend.app.core.logging import logger, request_id_var, generate_request_id
from backend.app.db.base import Base, get_engine
from backend.app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load model at startup, clean up on shutdown."""
    logger.info("Starting Image Quality Analyzer...")

    # Create database tables
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Load ML models
    from backend.app.services.inference import load_model
    try:
        predictor = load_model()
        v = predictor.metadata.get("model_version", "1.0.0")
        print("\n" + "=" * 62)
        print(f"  🟢 [MODEL STATUS: READY] Models loaded successfully! (v{v})")
        print("  🚀 Backend is fully ready to analyze images.")
        print("=" * 62 + "\n")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        print("\n" + "=" * 62)
        print(f"  🔴 [MODEL STATUS: NOT READY] {e}")
        print("  ⏳ Model artifacts are being generated in ml/artifacts/...")
        print("=" * 62 + "\n")

    yield

    logger.info("Shutting down Image Quality Analyzer...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Image Quality & Defect Detection API",
        description=(
            "AI-powered image quality assessment API. Upload images to detect "
            "blur, noise, exposure issues, compression artifacts, and other "
            "quality problems."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request, call_next):
        rid = generate_request_id()
        request_id_var.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    # Register routes
    app.include_router(api_router)

    return app


app = create_app()
