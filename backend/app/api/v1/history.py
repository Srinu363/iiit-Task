"""Analysis history endpoints.

GET /api/v1/analyses — List past analyses with pagination.
GET /api/v1/analyses/{id} — Get a single analysis by ID.
DELETE /api/v1/analyses/{id} — Delete an analysis.
"""

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.errors import NotFoundError
from backend.app.db.session import get_db
from backend.app.repositories.analysis_repo import AnalysisRepository
from backend.app.schemas.analysis import (
    AnalysisResponse,
    AnalysisListItem,
    AnalysisListResponse,
)

router = APIRouter(prefix="/api/v1", tags=["History"])


@router.get("/analyses", response_model=AnalysisListResponse)
def list_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    label: str | None = Query(None, description="Filter by quality label"),
    db: Session = Depends(get_db),
):
    """List past analyses with pagination and optional filtering by quality label."""
    repo = AnalysisRepository(db)
    analyses, total = repo.list_analyses(page, page_size, label)

    items = []
    for a in analyses:
        d = a.to_dict()
        items.append(AnalysisListItem(
            id=d["id"],
            filename=d["filename"],
            file_hash=d["file_hash"],
            created_at=d["created_at"],
            quality_score=d["quality_score"],
            quality_label=d["quality_label"],
            issues=d["issues"],
            latency_ms=d["latency_ms"],
            cached=d["cached"],
        ))

    total_pages = max(1, math.ceil(total / page_size))

    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Get a single analysis result by ID."""
    repo = AnalysisRepository(db)
    analysis = repo.get_by_id(analysis_id)
    if analysis is None:
        raise NotFoundError(f"Analysis '{analysis_id}' not found")
    return AnalysisResponse(**analysis.to_dict())


@router.delete("/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Delete an analysis by ID."""
    repo = AnalysisRepository(db)
    deleted = repo.delete(analysis_id)
    if not deleted:
        raise NotFoundError(f"Analysis '{analysis_id}' not found")
    return None
