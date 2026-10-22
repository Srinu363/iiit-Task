"""Noise estimation features.

Three complementary noise estimators:
- Immerkaer estimator: robust noise σ from Laplacian response
- Wavelet-based MAD: median absolute deviation of finest wavelet detail coefficients
- Flat-patch variance: variance in smooth (low-gradient) patches
"""

import cv2
import numpy as np
import pywt


def immerkaer_noise_estimate(gray: np.ndarray) -> float:
    """Immerkaer noise standard deviation estimator.

    Convolves with a specific Laplacian-like kernel and estimates
    noise σ from the result. Robust to image content because the
    operator suppresses low-frequency structure.

    Reference: Immerkaer, "Fast Noise Variance Estimation", CVIU 1996.
    """
    # 3×3 kernel from the Immerkaer paper
    kernel = np.array([
        [1, -2, 1],
        [-2, 4, -2],
        [1, -2, 1],
    ], dtype=np.float64)

    response = cv2.filter2D(gray.astype(np.float64), -1, kernel)
    h, w = gray.shape
    # Normalization factor
    sigma = np.sum(np.abs(response)) * np.sqrt(0.5 * np.pi) / (6.0 * (w - 2) * (h - 2))
    return float(sigma)


def wavelet_noise_estimate(gray: np.ndarray, wavelet: str = "db2") -> float:
    """Noise estimate via median absolute deviation of wavelet detail coefficients.

    The finest-scale diagonal detail coefficients (HH subband) capture
    mostly noise in natural images. MAD / 0.6745 gives a robust σ estimate.
    """
    coeffs = pywt.dwt2(gray.astype(np.float64), wavelet)
    # coeffs = (cA, (cH, cV, cD))
    _, (_, _, cD) = coeffs
    mad = np.median(np.abs(cD - np.median(cD)))
    # Robust sigma estimate
    sigma = mad / 0.6745
    return float(sigma)


def flat_patch_variance(gray: np.ndarray, patch_size: int = 32, num_patches: int = 20) -> float:
    """Average variance in the flattest patches of the image.

    Identifies low-gradient regions (flat patches) and measures their
    variance. In a noise-free image, flat patches have near-zero variance.
    High variance in flat patches indicates noise.
    """
    h, w = gray.shape
    if h < patch_size or w < patch_size:
        return 0.0

    gray_f = gray.astype(np.float64)

    # Compute gradient magnitude
    gx = cv2.Sobel(gray_f, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_f, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(gx**2 + gy**2)

    # Tile into patches and find the flattest ones
    step = patch_size
    patches = []
    for y in range(0, h - patch_size + 1, step):
        for x in range(0, w - patch_size + 1, step):
            patch_grad = grad_mag[y:y + patch_size, x:x + patch_size]
            patch_pixel = gray_f[y:y + patch_size, x:x + patch_size]
            patches.append((np.mean(patch_grad), np.var(patch_pixel)))

    if not patches:
        return 0.0

    # Sort by gradient magnitude (ascending) and take the flattest patches
    patches.sort(key=lambda p: p[0])
    n = min(num_patches, len(patches))
    avg_var = np.mean([p[1] for p in patches[:n]])
    return float(avg_var)


def extract_noise_features(gray: np.ndarray) -> dict[str, float]:
    """Extract all noise estimation features from a grayscale image."""
    return {
        "immerkaer_noise": immerkaer_noise_estimate(gray),
        "wavelet_noise": wavelet_noise_estimate(gray),
        "flat_patch_variance": flat_patch_variance(gray),
    }
