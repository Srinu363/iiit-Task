"""Pydantic-settings based configuration, all driven by environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    app_name: str = "Image Quality Analyzer"
    debug: bool = False
    backend_port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # File upload
    max_upload_size_mb: int = 20
    allowed_extensions: str = ".jpg,.jpeg,.png,.bmp,.webp,.tiff"
    upload_dir: str = "./uploads"

    # Model
    model_path: str = "./ml/artifacts"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_ext_list(self) -> list[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",")]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
