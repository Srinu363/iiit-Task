"""Inference service — singleton model wrapper for the backend.

Loads the ML prediction pipeline once at startup and provides
thread-safe inference.
"""

import sys
from pathlib import Path
from typing import Any

# Add project root so ml package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from ml.predict import QualityPredictor
from backend.app.core.config import settings
from backend.app.core.errors import InferenceError
from backend.app.core.logging import logger

_predictor: QualityPredictor | None = None


def load_model() -> QualityPredictor:
    """Load the model at startup. Called once from the lifespan handler."""
    global _predictor
    model_path = Path(settings.model_path)
    logger.info(f"Loading models from {model_path.resolve()}")

    try:
        _predictor = QualityPredictor.load(model_path)
        logger.info(f"Models loaded successfully (version: {_predictor.metadata.get('model_version')})")
        return _predictor
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


def get_predictor() -> QualityPredictor:
    """Get the loaded predictor instance."""
    if _predictor is None:
        raise InferenceError("Model not loaded. Server may be starting up.")
    return _predictor


def run_inference(image_bytes: bytes) -> dict[str, Any]:
    """Run inference on image bytes.

    Args:
        image_bytes: Raw image file bytes.

    Returns:
        Analysis result dict.

    Raises:
        InferenceError: If inference fails.
    """
    predictor = get_predictor()
    try:
        return predictor.predict_from_bytes(image_bytes)
    except ValueError as e:
        raise InferenceError(f"Image processing failed: {e}")
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise InferenceError(f"Model inference failed: {e}")


def get_model_info() -> dict:
    """Get model metadata."""
    predictor = get_predictor()
    return predictor.get_model_info()
