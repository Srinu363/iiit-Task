"""Feature extractor — combines all feature modules into a single fixed-order vector.

This is the main entry point for feature extraction. It loads an image,
computes all features from the submodules, and returns them as a dict
(preserving insertion order for consistent feature vectors).
"""

import cv2
import numpy as np

from ml.features.sharpness import extract_sharpness_features
from ml.features.exposure import extract_exposure_features
from ml.features.noise import extract_noise_features
from ml.features.contrast_color import extract_contrast_color_features
from ml.features.artifacts import extract_artifact_features


# Canonical feature order — must match training
FEATURE_ORDER = [
    # Sharpness (3)
    "laplacian_variance",
    "tenengrad",
    "fft_high_freq_ratio",
    # Exposure (8)
    "luminance_mean",
    "luminance_median",
    "luminance_std",
    "dark_clip_pct",
    "bright_clip_pct",
    "luminance_entropy",
    "dynamic_range",
    "luminance_skewness",
    # Noise (3)
    "immerkaer_noise",
    "wavelet_noise",
    "flat_patch_variance",
    # Contrast & Color (5)
    "rms_contrast",
    "michelson_contrast",
    "colorfulness",
    "saturation_mean",
    "saturation_std",
    # Artifacts & Texture (4)
    "blockiness",
    "edge_density",
    "spatial_entropy",
    "lbp_uniformity",
]


def load_and_preprocess(image_path: str, target_size: tuple[int, int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load an image and return (gray, bgr) arrays.

    Args:
        image_path: Path to the image file.
        target_size: Optional (width, height) to resize to.

    Returns:
        Tuple of (grayscale, BGR color) numpy arrays.

    Raises:
        ValueError: If the image cannot be loaded.
    """
    bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Cannot load image: {image_path}")

    if target_size is not None:
        bgr = cv2.resize(bgr, target_size, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return gray, bgr


def extract_features_from_arrays(gray: np.ndarray, bgr: np.ndarray) -> dict[str, float]:
    """Extract all features from pre-loaded image arrays.

    Args:
        gray: Grayscale image array (H, W).
        bgr: BGR color image array (H, W, 3).

    Returns:
        Dict of feature_name → value in canonical order.
    """
    features = {}
    features.update(extract_sharpness_features(gray))
    features.update(extract_exposure_features(gray))
    features.update(extract_noise_features(gray))
    features.update(extract_contrast_color_features(gray, bgr))
    features.update(extract_artifact_features(gray))
    return features


def extract_features(image_path: str, target_size: tuple[int, int] | None = None) -> dict[str, float]:
    """Extract all features from an image file.

    Args:
        image_path: Path to the image file.
        target_size: Optional resize dimensions.

    Returns:
        Dict of feature_name → value in canonical order.
    """
    gray, bgr = load_and_preprocess(image_path, target_size)
    return extract_features_from_arrays(gray, bgr)


def features_to_vector(features: dict[str, float]) -> np.ndarray:
    """Convert a feature dict to a fixed-order numpy vector."""
    return np.array([features[name] for name in FEATURE_ORDER], dtype=np.float64)


def extract_feature_vector(image_path: str, target_size: tuple[int, int] | None = None) -> np.ndarray:
    """Extract features and return as a fixed-order vector."""
    features = extract_features(image_path, target_size)
    return features_to_vector(features)
