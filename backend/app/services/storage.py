"""File storage service — manages uploaded images and deduplication."""

import shutil
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.logging import logger


def save_upload(data: bytes, file_hash: str, filename: str) -> Path:
    """Save uploaded file to disk, deduplicating by hash.

    Files are stored as {hash}_{original_name} so the same image
    uploaded with different names still deduplicates.

    Returns:
        Path to the saved file.
    """
    upload_dir = settings.upload_path
    safe_name = Path(filename).name  # Strip any path components
    dest = upload_dir / f"{file_hash[:16]}_{safe_name}"

    if dest.exists():
        logger.debug(f"File already exists: {dest}")
        return dest

    dest.write_bytes(data)
    logger.info(f"Saved upload: {dest} ({len(data)} bytes)")
    return dest


def get_upload_path(file_hash: str) -> Path | None:
    """Find an existing upload by hash prefix."""
    upload_dir = settings.upload_path
    prefix = file_hash[:16]
    for f in upload_dir.iterdir():
        if f.name.startswith(prefix):
            return f
    return None
