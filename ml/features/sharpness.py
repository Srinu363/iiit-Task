"""Sharpness feature extraction.

Derives three complementary measures of image sharpness:
- Laplacian variance: measures the second-derivative response (low → blurry)
- Tenengrad: Sobel gradient magnitude (low → blurry)
- FFT high-frequency ratio: fraction of spectral energy above the median frequency
"""

import cv2
import numpy as np


def laplacian_variance(gray: np.ndarray, ksize: int = 3) -> float:
    """Variance of the Laplacian — classic focus measure.

    A sharp image produces large second-derivative responses,
    yielding high variance. A blurry image has small, uniform responses.
    """
    lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=ksize)
    return float(np.var(lap))


def tenengrad(gray: np.ndarray, ksize: int = 3) -> float:
    """Tenengrad focus measure — mean squared Sobel gradient magnitude.

    Computes horizontal and vertical Sobel gradients and returns
    the mean of their squared sum. More robust to noise than Laplacian alone.
    """
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
    return float(np.mean(gx**2 + gy**2))


def fft_high_freq_ratio(gray: np.ndarray) -> float:
    """Ratio of high-frequency energy in the 2D FFT spectrum.

    Shifts FFT so DC is centered, then computes the fraction of
    total magnitude that lies beyond the median radius. Low ratio
    indicates loss of fine detail (blur).
    """
    f = np.fft.fft2(gray.astype(np.float64))
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)

    rows, cols = gray.shape
    crow, ccol = rows // 2, cols // 2

    # Build distance map from center
    y, x = np.ogrid[:rows, :cols]
    dist = np.sqrt((y - crow) ** 2 + (x - ccol) ** 2)

    # Median radius as cutoff
    max_radius = min(crow, ccol)
    cutoff = max_radius / 2

    total_energy = np.sum(magnitude)
    if total_energy < 1e-10:
        return 0.0

    high_freq_energy = np.sum(magnitude[dist > cutoff])
    return float(high_freq_energy / total_energy)


def extract_sharpness_features(gray: np.ndarray) -> dict[str, float]:
    """Extract all sharpness features from a grayscale image."""
    return {
        "laplacian_variance": laplacian_variance(gray),
        "tenengrad": tenengrad(gray),
        "fft_high_freq_ratio": fft_high_freq_ratio(gray),
    }
