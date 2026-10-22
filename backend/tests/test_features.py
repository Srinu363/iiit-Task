"""Tests for feature extraction modules."""

import numpy as np
import cv2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.features.sharpness import extract_sharpness_features
from ml.features.exposure import extract_exposure_features
from ml.features.noise import extract_noise_features
from ml.features.contrast_color import extract_contrast_color_features
from ml.features.artifacts import extract_artifact_features
from ml.features.extractor import extract_features_from_arrays, FEATURE_ORDER


def _make_test_image(h=200, w=300):
    """Create a test image with known properties."""
    bgr = np.random.randint(50, 200, (h, w, 3), dtype=np.uint8)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    return gray, bgr


def test_sharpness_features():
    """Sharpness features should return expected keys with numeric values."""
    gray, _ = _make_test_image()
    features = extract_sharpness_features(gray)
    assert "laplacian_variance" in features
    assert "tenengrad" in features
    assert "fft_high_freq_ratio" in features
    for v in features.values():
        assert isinstance(v, float)
        assert np.isfinite(v)


def test_exposure_features():
    """Exposure features should return expected keys."""
    gray, _ = _make_test_image()
    features = extract_exposure_features(gray)
    assert "luminance_mean" in features
    assert "dark_clip_pct" in features
    assert "bright_clip_pct" in features
    assert "luminance_entropy" in features
    assert 0 <= features["luminance_mean"] <= 255


def test_noise_features():
    """Noise features should return non-negative values."""
    gray, _ = _make_test_image()
    features = extract_noise_features(gray)
    assert "immerkaer_noise" in features
    assert "wavelet_noise" in features
    assert features["immerkaer_noise"] >= 0
    assert features["wavelet_noise"] >= 0


def test_contrast_color_features():
    """Contrast/color features should return expected keys."""
    gray, bgr = _make_test_image()
    features = extract_contrast_color_features(gray, bgr)
    assert "rms_contrast" in features
    assert "colorfulness" in features
    assert "saturation_mean" in features


def test_artifact_features():
    """Artifact features should return expected keys."""
    gray, _ = _make_test_image()
    features = extract_artifact_features(gray)
    assert "blockiness" in features
    assert "edge_density" in features
    assert "spatial_entropy" in features
    assert "lbp_uniformity" in features


def test_full_extractor():
    """Full extractor should produce all features in canonical order."""
    gray, bgr = _make_test_image()
    features = extract_features_from_arrays(gray, bgr)

    for name in FEATURE_ORDER:
        assert name in features, f"Missing feature: {name}"
        assert isinstance(features[name], float), f"Non-float feature: {name}"
        assert np.isfinite(features[name]), f"Non-finite feature: {name}"


def test_blurry_vs_sharp():
    """Blurred image should have lower sharpness than sharp image."""
    gray, _ = _make_test_image()
    sharp_features = extract_sharpness_features(gray)

    blurry = cv2.GaussianBlur(gray, (21, 21), 5)
    blur_features = extract_sharpness_features(blurry)

    assert blur_features["laplacian_variance"] < sharp_features["laplacian_variance"]
    assert blur_features["tenengrad"] < sharp_features["tenengrad"]


def test_dark_vs_bright():
    """Dark image should have lower luminance than bright image."""
    dark = np.full((100, 100), 5, dtype=np.uint8)     # below dark_clip threshold (10)
    bright = np.full((100, 100), 250, dtype=np.uint8)  # above bright_clip threshold (245)

    dark_features = extract_exposure_features(dark)
    bright_features = extract_exposure_features(bright)

    assert dark_features["luminance_mean"] < bright_features["luminance_mean"]
    assert dark_features["dark_clip_pct"] > bright_features["dark_clip_pct"]
