"""Patch-level quality heatmaps.

Computes per-patch quality metrics and generates heatmaps that
localize blur, noise, exposure, and contrast issues spatially.
"""

import cv2
import numpy as np
from ml.features.sharpness import laplacian_variance, tenengrad
from ml.features.noise import immerkaer_noise_estimate
from ml.features.exposure import luminance_stats


def compute_patch_heatmaps(gray: np.ndarray, patch_size: int = 64) -> dict[str, np.ndarray]:
    """Compute per-patch quality heatmaps.

    Divides the image into patches and computes quality metrics
    for each patch, producing heatmaps that show spatial variation
    in quality.

    Args:
        gray: Grayscale image (H, W).
        patch_size: Size of each square patch.

    Returns:
        Dict mapping metric name → heatmap array (rows, cols) where
        each cell is the metric value for that patch.
    """
    h, w = gray.shape
    rows = h // patch_size
    cols = w // patch_size

    heatmaps = {
        "sharpness": np.zeros((rows, cols), dtype=np.float64),
        "noise": np.zeros((rows, cols), dtype=np.float64),
        "brightness": np.zeros((rows, cols), dtype=np.float64),
        "contrast": np.zeros((rows, cols), dtype=np.float64),
    }

    for r in range(rows):
        for c in range(cols):
            y1 = r * patch_size
            y2 = y1 + patch_size
            x1 = c * patch_size
            x2 = x1 + patch_size
            patch = gray[y1:y2, x1:x2]

            # Sharpness: Laplacian variance (higher = sharper)
            heatmaps["sharpness"][r, c] = laplacian_variance(patch)

            # Noise: Immerkaer estimate (higher = noisier)
            heatmaps["noise"][r, c] = immerkaer_noise_estimate(patch)

            # Brightness: mean luminance
            heatmaps["brightness"][r, c] = float(np.mean(patch))

            # Contrast: local standard deviation
            heatmaps["contrast"][r, c] = float(np.std(patch))

    return heatmaps


def heatmap_to_overlay(heatmap: np.ndarray, image_shape: tuple[int, int],
                        colormap: int = cv2.COLORMAP_JET,
                        alpha: float = 0.4,
                        invert: bool = False) -> np.ndarray:
    """Convert a patch heatmap to a full-resolution color overlay.

    Args:
        heatmap: Patch heatmap (rows, cols).
        image_shape: (H, W) of the original image.
        colormap: OpenCV colormap to use.
        alpha: Overlay transparency.
        invert: If True, invert the heatmap (high values → cold colors).

    Returns:
        BGR overlay image at the original resolution.
    """
    h, w = image_shape

    # Normalize to 0-255
    hm = heatmap.astype(np.float64)
    hm_min, hm_max = hm.min(), hm.max()
    if hm_max - hm_min > 1e-10:
        hm = (hm - hm_min) / (hm_max - hm_min) * 255
    else:
        hm = np.zeros_like(hm)

    if invert:
        hm = 255 - hm

    hm = hm.astype(np.uint8)

    # Resize to original image dimensions
    hm_resized = cv2.resize(hm, (w, h), interpolation=cv2.INTER_LINEAR)

    # Apply colormap
    colored = cv2.applyColorMap(hm_resized, colormap)
    return colored


def generate_heatmap_overlays(gray: np.ndarray, bgr: np.ndarray,
                               patch_size: int = 64) -> dict[str, np.ndarray]:
    """Generate all heatmap overlays for an image.

    Returns:
        Dict mapping metric name → BGR overlay image with heatmap blended.
    """
    heatmaps = compute_patch_heatmaps(gray, patch_size)
    h, w = gray.shape
    overlays = {}

    for name, hm in heatmaps.items():
        # Sharpness: invert so low sharpness = hot colors (red = problem)
        # Noise: high noise = hot colors (red = problem)
        # Brightness: show as-is (yellow/red = bright, blue = dark)
        # Contrast: invert so low contrast = hot colors
        invert = name in ("sharpness", "contrast")

        colored = heatmap_to_overlay(hm, (h, w), invert=invert)
        overlay = cv2.addWeighted(bgr, 0.6, colored, 0.4, 0)
        overlays[name] = overlay

    return overlays
