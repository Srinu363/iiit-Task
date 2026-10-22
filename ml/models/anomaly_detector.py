"""Anomaly detector for 'potential visual defect' and 'severe degradation'.

Uses Isolation Forest trained only on clean/high-quality images.
Images that deviate significantly from the clean distribution
are flagged as anomalous — indicating potential defects or
severe degradation that doesn't fit known issue categories.
"""

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.config import IFOREST_PARAMS
from ml.features.extractor import FEATURE_ORDER


class AnomalyDetector:
    """Isolation Forest trained on clean images to detect anomalous quality.

    The model learns the distribution of features from pristine reference
    images. At inference, images with features far from this distribution
    receive low anomaly scores, indicating potential defects.
    """

    def __init__(self, iforest_params: dict | None = None):
        params = iforest_params or IFOREST_PARAMS.copy()
        self.model = IsolationForest(**params)
        self.scaler = StandardScaler()
        self.feature_names = FEATURE_ORDER
        self._is_fitted = False

    def fit(self, X_clean: np.ndarray) -> dict:
        """Train on clean/reference images only.

        Args:
            X_clean: Feature matrix of clean images (n_clean, n_features).

        Returns:
            Training info dict.
        """
        X_scaled = self.scaler.fit_transform(X_clean)
        self.model.fit(X_scaled)
        self._is_fitted = True

        # Get anomaly scores on training data for threshold calibration
        scores = self.model.decision_function(X_scaled)
        return {
            "n_clean_samples": X_clean.shape[0],
            "mean_clean_score": float(np.mean(scores)),
            "std_clean_score": float(np.std(scores)),
            "min_clean_score": float(np.min(scores)),
        }

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Predict anomaly labels and scores.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Tuple of:
              - is_anomaly: boolean array (True = anomalous)
              - anomaly_score: float array (lower = more anomalous,
                converted to 0-1 range where 1 = most anomalous)
        """
        X_scaled = self.scaler.transform(X)

        # decision_function: negative = anomaly, positive = normal
        raw_scores = self.model.decision_function(X_scaled)
        labels = self.model.predict(X_scaled)  # 1 = normal, -1 = anomaly

        is_anomaly = labels == -1

        # Convert to 0-1 range: higher = more anomalous
        # Sigmoid-like transformation centered at 0
        anomaly_score = 1.0 / (1.0 + np.exp(raw_scores * 5))

        return is_anomaly, anomaly_score

    def predict_single(self, X: np.ndarray) -> tuple[bool, float]:
        """Predict anomaly for a single sample."""
        is_anom, score = self.predict(X.reshape(1, -1))
        return bool(is_anom[0]), float(score[0])
