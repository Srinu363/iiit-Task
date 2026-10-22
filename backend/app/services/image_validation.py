"""Image validation service.

Validates uploaded images by checking:
- File extension against allowlist
- Magic bytes (file signature) to verify actual file type
- File size against configurable limit
- Decodability with OpenCV
- Sane image dimensions
"""

import hashlib
from pathlib import Path

import cv2
import numpy as np

from backend.app.core.config import settings
from backend.app.core.errors import (
    ImageValidationError,
    FileTooLargeError,
    UnsupportedMediaError,
)

# Magic bytes for common image formats
MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"BM": "bmp",
    b"RIFF": "webp",  # WebP starts with RIFF....WEBP
    b"II\x2a\x00": "tiff",  # Little-endian TIFF
    b"MM\x00\x2a": "tiff",  # Big-endian TIFF
}

MAX_DIMENSION = 10000  # Max width or height in pixels
MIN_DIMENSION = 16     # Minimum width or height


def validate_extension(filename: str) -> str:
    """Validate file extension and return the normalized extension.

    Raises:
        UnsupportedMediaError: If extension is not in the allowlist.
    """
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_ext_list:
        raise UnsupportedMediaError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.allowed_ext_list)}"
        )
    return ext


def validate_magic_bytes(data: bytes) -> str:
    """Check file magic bytes to verify actual file type.

    Returns:
        Detected file type string.

    Raises:
        UnsupportedMediaError: If magic bytes don't match any known format.
    """
    for magic, fmt in MAGIC_BYTES.items():
        if data[:len(magic)] == magic:
            return fmt
    raise UnsupportedMediaError(
        "File content does not match any supported image format (magic bytes check failed)"
    )


def validate_size(data: bytes) -> None:
    """Check file size against the configured limit.

    Raises:
        FileTooLargeError: If file exceeds the maximum size.
    """
    if len(data) > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"File size {len(data) / (1024*1024):.1f}MB exceeds "
            f"maximum of {settings.max_upload_size_mb}MB"
        )


def validate_decodable(data: bytes) -> np.ndarray:
    """Verify the image can be decoded by OpenCV.

    Returns:
        Decoded BGR image array.

    Raises:
        ImageValidationError: If the image cannot be decoded.
    """
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ImageValidationError(
            "Image file is corrupted or cannot be decoded"
        )
    return img


def validate_dimensions(img: np.ndarray) -> None:
    """Check image dimensions are within acceptable bounds.

    Raises:
        ImageValidationError: If dimensions are outside acceptable range.
    """
    h, w = img.shape[:2]
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        raise ImageValidationError(
            f"Image dimensions {w}×{h} exceed maximum of {MAX_DIMENSION}×{MAX_DIMENSION}"
        )
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        raise ImageValidationError(
            f"Image dimensions {w}×{h} are below minimum of {MIN_DIMENSION}×{MIN_DIMENSION}"
        )


def compute_file_hash(data: bytes) -> str:
    """Compute SHA-256 hash of file data for deduplication."""
    return hashlib.sha256(data).hexdigest()


def validate_image(filename: str, data: bytes) -> tuple[np.ndarray, str]:
    """Run all validations on an uploaded image.

    Args:
        filename: Original filename.
        data: Raw file bytes.

    Returns:
        Tuple of (decoded BGR image, file hash).

    Raises:
        Various AppError subclasses on validation failure.
    """
    validate_extension(filename)
    validate_size(data)
    validate_magic_bytes(data)
    img = validate_decodable(data)
    validate_dimensions(img)
    file_hash = compute_file_hash(data)
    return img, file_hash
