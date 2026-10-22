"""Artifact and texture feature extraction.

Detects compression artifacts and texture anomalies:
- Blockiness: DCT-based JPEG artifact measure
- Edge density: fraction of edge pixels (Canny)
- Local entropy: spatial entropy in a neighborhood
- LBP texture uniformity: Local Binary Pattern histogram uniformity
"""

import cv2
import numpy as np
from skimage.feature import local_binary_pattern
from skimage.filters.rank import entropy as rank_entropy
from skimage.morphology import disk


def blockiness_measure(gray: np.ndarray, block_size: int = 8) -> float:
    """Estimate JPEG-like blockiness.

    Measures the average absolute difference across 8×8 block boundaries.
    High blockiness indicates JPEG compression artifacts.
    """
    gray_f = gray.astype(np.float64)
    h, w = gray_f.shape

    # Horizontal block boundaries
    h_diffs = []
    for x in range(block_size, w - 1, block_size):
        diff = np.abs(gray_f[:, x] - gray_f[:, x - 1])
        h_diffs.append(np.mean(diff))

    # Vertical block boundaries
    v_diffs = []
    for y in range(block_size, h - 1, block_size):
        diff = np.abs(gray_f[y, :] - gray_f[y - 1, :])
        v_diffs.append(np.mean(diff))

    all_diffs = h_diffs + v_diffs
    if not all_diffs:
        return 0.0

    # Also compute average difference at non-boundary positions for normalization
    non_boundary_h = []
    for x in range(1, w - 1):
        if x % block_size != 0:
            diff = np.abs(gray_f[:, x] - gray_f[:, x - 1])
            non_boundary_h.append(np.mean(diff))
            if len(non_boundary_h) >= 50:
                break

    avg_boundary = np.mean(all_diffs)
    avg_non_boundary = np.mean(non_boundary_h) if non_boundary_h else 1.0

    if avg_non_boundary < 1e-10:
        return 0.0

    # Ratio > 1 indicates block artifacts
    return float(avg_boundary / avg_non_boundary)


def edge_density(gray: np.ndarray) -> float:
    """Fraction of pixels detected as edges by Canny.

    Very low edge density may indicate excessive blur or smoothing.
    Very high edge density may indicate noise or oversharpening.
    """
    edges = cv2.Canny(gray, 50, 150)
    return float(np.sum(edges > 0) / edges.size)


def spatial_entropy(gray: np.ndarray) -> float:
    """Mean local entropy computed over a disk neighborhood.

    Uses skimage's rank entropy with a disk of radius 5.
    Low local entropy regions indicate uniform/flat areas;
    the global mean captures overall texture complexity.
    """
    # Resize for speed if image is large
    h, w = gray.shape
    if max(h, w) > 256:
        scale = 256 / max(h, w)
        small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    else:
        small = gray

    ent = rank_entropy(small, disk(5))
    return float(np.mean(ent))


def lbp_uniformity(gray: np.ndarray, radius: int = 2, n_points: int = 16) -> float:
    """Uniformity of the Local Binary Pattern histogram.

    LBP captures local texture patterns. The uniformity (sum of squared
    probabilities) is high when the texture is regular and low when
    there are many different texture patterns (e.g., noise or artifacts).
    """
    # Resize for speed
    h, w = gray.shape
    if max(h, w) > 256:
        scale = 256 / max(h, w)
        small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    else:
        small = gray

    lbp = local_binary_pattern(small, n_points, radius, method="uniform")
    n_bins = n_points + 2  # uniform LBP has P+2 bins
    hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins), density=True)
    uniformity = float(np.sum(hist**2))
    return uniformity


def extract_artifact_features(gray: np.ndarray) -> dict[str, float]:
    """Extract all artifact/texture features from a grayscale image."""
    return {
        "blockiness": blockiness_measure(gray),
        "edge_density": edge_density(gray),
        "spatial_entropy": spatial_entropy(gray),
        "lbp_uniformity": lbp_uniformity(gray),
    }
