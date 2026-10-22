"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services.inference import get_predictor
from backend.app.schemas.analysis import HealthResponse, ModelInfoResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Service health check — verifies model and database are operational."""
    model_loaded = False
    try:
        get_predictor()
        model_loaded = True
    except Exception:
        pass

    db_connected = False
    try:
        db.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
        db_connected = True
    except Exception:
        pass

    status = "healthy" if (model_loaded and db_connected) else "degraded"
    return HealthResponse(
        status=status,
        model_loaded=model_loaded,
        database_connected=db_connected,
        version=settings.app_name,
    )


@router.get("/api/v1/model-info", response_model=ModelInfoResponse, tags=["Health"])
def model_info():
    """Return model metadata and configuration."""
    from backend.app.services.inference import get_model_info
    info = get_model_info()
    return ModelInfoResponse(**info)
