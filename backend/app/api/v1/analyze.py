"""Image analysis endpoints.

POST /api/v1/analyze — Upload and analyze a single image.
POST /api/v1/analyze/batch — Upload and analyze multiple images.
"""

import asyncio
import math
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.errors import ImageValidationError, InferenceError
from backend.app.core.logging import logger
from backend.app.db.session import get_db
from backend.app.repositories.analysis_repo import AnalysisRepository
from backend.app.schemas.analysis import AnalysisResponse
from backend.app.services.image_validation import validate_image
from backend.app.services.inference import run_inference
from backend.app.services.storage import save_upload

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# Thread pool for CPU-bound inference (keeps event loop responsive)
_executor = ThreadPoolExecutor(max_workers=4)


@router.post("/analyze", response_model=AnalysisResponse, status_code=201)
async def analyze_image(
    file: UploadFile = File(..., description="Image file to analyze"),
    db: Session = Depends(get_db),
):
    """Upload and analyze a single image.

    Validates the uploaded file, runs ML inference in a thread pool,
    and persists the result. Returns cached result if the same image
    (by SHA-256 hash) was previously analyzed.
    """
    if not file.filename:
        raise ImageValidationError("No filename provided")

    # Read file bytes
    data = await file.read()
    if not data:
        raise ImageValidationError("Empty file uploaded")

    # Validate image
    _, file_hash = validate_image(file.filename, data)

    # Check for cached result (deduplication)
    repo = AnalysisRepository(db)
    cached = repo.get_by_hash(file_hash)
    if cached:
        logger.info(f"Cache hit for {file.filename} (hash: {file_hash[:16]})")
        cached.cached = True
        result = cached.to_dict()
        return AnalysisResponse(**result)

    # Save the upload
    save_upload(data, file_hash, file.filename)

    # Run inference in thread pool to not block the event loop
    loop = asyncio.get_event_loop()
    try:
        analysis_result = await loop.run_in_executor(_executor, run_inference, data)
    except InferenceError:
        raise
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        raise InferenceError(f"Analysis failed: {e}")

    # Persist result
    analysis_data = {
        "filename": file.filename,
        "file_hash": file_hash,
        "quality_score": analysis_result["quality_score"],
        "quality_label": analysis_result["quality_label"],
        "issues": analysis_result["issues"],
        "image_stats": analysis_result["image_stats"],
        "explanations": analysis_result["explanations"],
        "feature_importance": analysis_result["feature_importance"],
        "heatmaps": analysis_result.get("heatmaps"),
        "anomaly_score": analysis_result.get("anomaly_score"),
        "model_version": analysis_result.get("model_version"),
        "latency_ms": analysis_result.get("latency_ms"),
        "cached": False,
    }
    analysis = repo.create(analysis_data)

    return AnalysisResponse(**analysis.to_dict())


@router.post("/analyze/batch", response_model=list[AnalysisResponse], status_code=201)
async def analyze_batch(
    files: list[UploadFile] = File(..., description="Image files to analyze (max 10)"),
    db: Session = Depends(get_db),
):
    """Upload and analyze multiple images (up to 10).

    Processes images sequentially to manage memory usage.
    Returns a list of analysis results.
    """
    if len(files) > 10:
        raise ImageValidationError("Maximum 10 files per batch request")

    results = []
    for file in files:
        if not file.filename:
            continue

        data = await file.read()
        if not data:
            continue

        try:
            _, file_hash = validate_image(file.filename, data)

            repo = AnalysisRepository(db)
            cached = repo.get_by_hash(file_hash)
            if cached:
                cached.cached = True
                results.append(AnalysisResponse(**cached.to_dict()))
                continue

            save_upload(data, file_hash, file.filename)

            loop = asyncio.get_event_loop()
            analysis_result = await loop.run_in_executor(_executor, run_inference, data)

            analysis_data = {
                "filename": file.filename,
                "file_hash": file_hash,
                "quality_score": analysis_result["quality_score"],
                "quality_label": analysis_result["quality_label"],
                "issues": analysis_result["issues"],
                "image_stats": analysis_result["image_stats"],
                "explanations": analysis_result["explanations"],
                "feature_importance": analysis_result["feature_importance"],
                "heatmaps": analysis_result.get("heatmaps"),
                "anomaly_score": analysis_result.get("anomaly_score"),
                "model_version": analysis_result.get("model_version"),
                "latency_ms": analysis_result.get("latency_ms"),
                "cached": False,
            }
            analysis = repo.create(analysis_data)
            results.append(AnalysisResponse(**analysis.to_dict()))
        except Exception as e:
            logger.error(f"Batch analysis failed for {file.filename}: {e}")
            # Continue processing remaining files

    return results
