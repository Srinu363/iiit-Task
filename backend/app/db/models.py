"""SQLAlchemy ORM models for analysis persistence."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, Boolean
from sqlalchemy.types import TypeDecorator
import json

from backend.app.db.base import Base


class JSONType(TypeDecorator):
    """Store JSON data as text in SQLite, native JSON in PostgreSQL."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


class Analysis(Base):
    """Persisted image analysis result."""

    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Quality assessment
    quality_score = Column(Float, nullable=False)
    quality_label = Column(String(20), nullable=False, index=True)

    # Detected issues (JSON array)
    issues = Column(JSONType, nullable=False, default=list)

    # Image statistics (JSON object)
    image_stats = Column(JSONType, nullable=True)

    # Explanations (JSON array of strings)
    explanations = Column(JSONType, nullable=True)

    # Feature importance (JSON array)
    feature_importance = Column(JSONType, nullable=True)

    # Heatmap data (JSON — can be large)
    heatmaps = Column(JSONType, nullable=True)

    # Anomaly score
    anomaly_score = Column(Float, nullable=True)

    # Model version used
    model_version = Column(String(20), nullable=True)

    # Processing time in milliseconds
    latency_ms = Column(Float, nullable=True)

    # Whether this was a cached result
    cached = Column(Boolean, default=False)

    def to_dict(self) -> dict:
        """Convert to API response dict."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_hash": self.file_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "quality_score": self.quality_score,
            "quality_label": self.quality_label,
            "issues": self.issues or [],
            "image_stats": self.image_stats or {},
            "explanations": self.explanations or [],
            "feature_importance": self.feature_importance or [],
            "heatmaps": self.heatmaps,
            "anomaly_score": self.anomaly_score,
            "model_version": self.model_version,
            "latency_ms": self.latency_ms,
            "cached": self.cached or False,
        }
