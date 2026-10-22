"""Contrast and color feature extraction.

Measures contrast characteristics and color properties:
- RMS contrast: standard deviation of luminance
- Michelson contrast: (max-min)/(max+min) on luminance
- Saturation statistics: mean, std of saturation channel
- Colorfulness: Hasler & Süsstrunk metric
"""

import cv2
import numpy as np


def rms_contrast(gray: np.ndarray) -> float:
    """RMS contrast — standard deviation of pixel intensities.

    A simple but effective measure. Low RMS contrast indicates
    a flat, washed-out image.
    """
    return float(np.std(gray.astype(np.float64)))


def michelson_contrast(gray: np.ndarray) -> float:
    """Michelson contrast: (Imax - Imin) / (Imax + Imin).

    Ranges from 0 (no contrast) to 1 (maximum contrast).
    Sensitive to outlier pixels, so we use 1st/99th percentiles.
    """
    low = float(np.percentile(gray, 1))
    high = float(np.percentile(gray, 99))
    denom = high + low
    if denom < 1e-10:
        return 0.0
    return float((high - low) / denom)


def saturation_stats(bgr: np.ndarray) -> dict[str, float]:
    """Mean and standard deviation of the saturation channel (HSV)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1].astype(np.float64)
    return {
        "saturation_mean": float(np.mean(s)),
        "saturation_std": float(np.std(s)),
    }


def colorfulness(bgr: np.ndarray) -> float:
    """Hasler & Süsstrunk colorfulness metric.

    Computes opponent color channels (rg, yb) and combines their
    statistics. Higher values indicate more vivid colors.
    Low colorfulness can indicate desaturation or color artifacts.

    Reference: Hasler & Süsstrunk, "Measuring Colourfulness in
    Natural Images", SPIE 2003.
    """
    b, g, r = (bgr[:, :, i].astype(np.float64) for i in range(3))

    rg = r - g
    yb = 0.5 * (r + g) - b

    rg_mean, rg_std = np.mean(rg), np.std(rg)
    yb_mean, yb_std = np.mean(yb), np.std(yb)

    std_root = np.sqrt(rg_std**2 + yb_std**2)
    mean_root = np.sqrt(rg_mean**2 + yb_mean**2)

    return float(std_root + 0.3 * mean_root)


def extract_contrast_color_features(gray: np.ndarray, bgr: np.ndarray) -> dict[str, float]:
    """Extract all contrast and color features."""
    features = {
        "rms_contrast": rms_contrast(gray),
        "michelson_contrast": michelson_contrast(gray),
        "colorfulness": colorfulness(bgr),
    }
    features.update(saturation_stats(bgr))
    return features
