"""Analysis repository — database operations for Analysis records."""

import math
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db.models import Analysis


class AnalysisRepository:
    """CRUD operations for Analysis records."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, analysis_data: dict) -> Analysis:
        """Create a new analysis record."""
        analysis = Analysis(**analysis_data)
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_by_id(self, analysis_id: str) -> Analysis | None:
        """Get a single analysis by ID."""
        return self.db.query(Analysis).filter(Analysis.id == analysis_id).first()

    def get_by_hash(self, file_hash: str) -> Analysis | None:
        """Find an existing analysis by file hash (for deduplication)."""
        return (
            self.db.query(Analysis)
            .filter(Analysis.file_hash == file_hash)
            .order_by(desc(Analysis.created_at))
            .first()
        )

    def list_analyses(
        self,
        page: int = 1,
        page_size: int = 20,
        quality_label: str | None = None,
    ) -> tuple[list[Analysis], int]:
        """List analyses with pagination and optional filtering.

        Returns:
            Tuple of (analyses list, total count).
        """
        query = self.db.query(Analysis)

        if quality_label:
            query = query.filter(Analysis.quality_label == quality_label.upper())

        total = query.count()
        analyses = (
            query.order_by(desc(Analysis.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return analyses, total

    def delete(self, analysis_id: str) -> bool:
        """Delete an analysis by ID. Returns True if deleted."""
        analysis = self.get_by_id(analysis_id)
        if analysis is None:
            return False
        self.db.delete(analysis)
        self.db.commit()
        return True
