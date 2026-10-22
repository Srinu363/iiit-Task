"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from pydantic import BaseModel, Field


class IssueResponse(BaseModel):
    """Single detected quality issue."""
    type: str = Field(..., description="Issue type (blur, noise, etc.)")
    severity: str = Field(..., description="Severity level: low, medium, high")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    uncertain: bool = Field(False, description="Whether prediction is near decision boundary")


class AnalysisResponse(BaseModel):
    """Complete analysis result returned by the API."""
    id: str
    filename: str
    file_hash: str
    created_at: datetime | None = None
    quality_score: float = Field(..., ge=0, le=100)
    quality_label: str = Field(..., description="ACCEPTABLE, DEGRADED, or DEFECTIVE")
    issues: list[IssueResponse] = []
    image_stats: dict = {}
    explanations: list[str] = []
    feature_importance: list[dict] = []
    heatmaps: dict | None = None
    anomaly_score: float | None = None
    model_version: str | None = None
    latency_ms: float | None = None
    cached: bool = False


class AnalysisListItem(BaseModel):
    """Summary item for the history list (no heatmaps to reduce payload)."""
    id: str
    filename: str
    file_hash: str
    created_at: datetime | None = None
    quality_score: float
    quality_label: str
    issues: list[IssueResponse] = []
    latency_ms: float | None = None
    cached: bool = False


class AnalysisListResponse(BaseModel):
    """Paginated list of analyses."""
    items: list[AnalysisListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    database_connected: bool
    version: str


class ModelInfoResponse(BaseModel):
    """Model metadata response."""
    model_version: str | None = None
    training_date: str | None = None
    num_features: int | None = None
    feature_names: list[str] = []
    issue_types: list[str] = []
    training_samples: int | None = None
    regressor_metrics: dict | None = None


class ErrorDetail(BaseModel):
    """Error detail."""
    code: str
    message: str
    request_id: str = ""


class ErrorResponse(BaseModel):
    """Consistent error response."""
    error: ErrorDetail
