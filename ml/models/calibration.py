"""Probability calibration and uncertainty estimation.

Applies isotonic regression calibration to raw model probabilities
and provides uncertainty flags when predictions are near decision boundaries.
"""

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression


class ConfidenceCalibrator:
    """Calibrates raw probabilities using isotonic regression.

    Raw classifier probabilities are often miscalibrated (overconfident
    or underconfident). This module fits a monotonic mapping from raw
    probabilities to calibrated ones using a validation set.
    """

    def __init__(self, uncertainty_threshold: float = 0.15):
        """
        Args:
            uncertainty_threshold: Distance from 0.5 below which
                predictions are flagged as uncertain.
                E.g., 0.15 means probabilities in [0.35, 0.65] are uncertain.
        """
        self.calibrators: dict[str, IsotonicRegression] = {}
        self.uncertainty_threshold = uncertainty_threshold

    def fit(self, probas: dict[str, np.ndarray], y_true: dict[str, np.ndarray]) -> dict:
        """Fit isotonic regression calibrators per issue type.

        Args:
            probas: Dict of issue_type → raw probability array.
            y_true: Dict of issue_type → binary label array.

        Returns:
            Calibration metrics per issue type.
        """
        metrics = {}
        for issue_type in probas:
            if issue_type not in y_true:
                continue

            p = probas[issue_type]
            y = y_true[issue_type]

            if len(np.unique(y)) < 2:
                continue

            iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            iso.fit(p, y)
            self.calibrators[issue_type] = iso

            # Compute ECE (Expected Calibration Error)
            p_cal = iso.predict(p)
            ece = self._compute_ece(p_cal, y)
            metrics[issue_type] = {"ece": round(ece, 4)}

        return metrics

    def calibrate(self, probas: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """Calibrate raw probabilities.

        Args:
            probas: Dict of issue_type → raw probability array.

        Returns:
            Dict of issue_type → calibrated probability array.
        """
        calibrated = {}
        for issue_type, p in probas.items():
            if issue_type in self.calibrators:
                calibrated[issue_type] = self.calibrators[issue_type].predict(p)
            else:
                calibrated[issue_type] = p
        return calibrated

    def is_uncertain(self, confidence: float) -> bool:
        """Check if a prediction confidence is in the uncertain zone."""
        return abs(confidence - 0.5) < self.uncertainty_threshold

    @staticmethod
    def _compute_ece(probas: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error.

        Bins predictions, computes the gap between average confidence
        and actual accuracy in each bin, weighted by bin population.
        """
        bin_edges = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (probas >= bin_edges[i]) & (probas < bin_edges[i + 1])
            if mask.sum() == 0:
                continue
            bin_conf = probas[mask].mean()
            bin_acc = labels[mask].mean()
            ece += mask.sum() / len(probas) * abs(bin_conf - bin_acc)
        return ece
