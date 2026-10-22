"""Exposure and brightness feature extraction.

Measures brightness characteristics to detect under/overexposure:
- Mean/median luminance in 0–255 range
- Histogram clipping percentages (how much is crushed to black/white)
- Luminance entropy (information content)
- Dynamic range (spread of intensity values)
"""

import cv2
import numpy as np
from scipy import stats as sp_stats


def luminance_stats(gray: np.ndarray) -> dict[str, float]:
    """Basic luminance statistics."""
    return {
        "luminance_mean": float(np.mean(gray)),
        "luminance_median": float(np.median(gray)),
        "luminance_std": float(np.std(gray)),
    }


def histogram_clipping(gray: np.ndarray, low_thresh: int = 10, high_thresh: int = 245) -> dict[str, float]:
    """Percentage of pixels clipped to near-black or near-white.

    High dark_clip → underexposed. High bright_clip → overexposed.
    Images with healthy exposure have low values for both.
    """
    total = gray.size
    dark_clip = float(np.sum(gray <= low_thresh) / total)
    bright_clip = float(np.sum(gray >= high_thresh) / total)
    return {
        "dark_clip_pct": dark_clip,
        "bright_clip_pct": bright_clip,
    }


def luminance_entropy(gray: np.ndarray) -> float:
    """Shannon entropy of the luminance histogram.

    Low entropy indicates a narrow intensity distribution
    (e.g., very dark or very bright images with little variation).
    """
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist = hist / hist.sum()
    # Filter zero bins to avoid log(0)
    hist = hist[hist > 0]
    return float(-np.sum(hist * np.log2(hist)))


def dynamic_range(gray: np.ndarray, percentile: float = 1.0) -> float:
    """Effective dynamic range: difference between 99th and 1st percentile.

    Using percentiles instead of min/max avoids sensitivity to outlier pixels.
    """
    low = np.percentile(gray, percentile)
    high = np.percentile(gray, 100 - percentile)
    return float(high - low)


def luminance_skewness(gray: np.ndarray) -> float:
    """Skewness of luminance distribution.

    Positive skew → predominantly dark (underexposed).
    Negative skew → predominantly bright (overexposed).
    """
    return float(sp_stats.skew(gray.ravel()))


def extract_exposure_features(gray: np.ndarray) -> dict[str, float]:
    """Extract all exposure-related features from a grayscale image."""
    features = {}
    features.update(luminance_stats(gray))
    features.update(histogram_clipping(gray))
    features["luminance_entropy"] = luminance_entropy(gray)
    features["dynamic_range"] = dynamic_range(gray)
    features["luminance_skewness"] = luminance_skewness(gray)
    return features
