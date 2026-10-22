"""Quality score regressor.

Predicts a continuous quality score (0-100) from image features.
Uses LightGBM regression trained on DMOS-derived scores.
"""

import sys
from pathlib import Path

import numpy as np
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.config import LGBM_PARAMS
from ml.features.extractor import FEATURE_ORDER


class QualityRegressor:
    """Predicts image quality score (0-100) using gradient boosting regression."""

    def __init__(self, lgbm_params: dict | None = None):
        params = (lgbm_params or LGBM_PARAMS).copy()
        params["objective"] = "regression"
        params["metric"] = "mae"
        # Remove classification-specific params
        params.pop("scale_pos_weight", None)
        self.regressor = LGBMRegressor(**params)
        self.scaler = StandardScaler()
        self.feature_names = FEATURE_ORDER

    def fit(self, X: np.ndarray, y: np.ndarray,
            X_val: np.ndarray | None = None,
            y_val: np.ndarray | None = None) -> dict:
        """Train the quality regressor.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Quality scores (n_samples,) in range [0, 100].
            X_val: Optional validation features.
            y_val: Optional validation scores.

        Returns:
            Training metrics dict.
        """
        X_scaled = self.scaler.fit_transform(X)

        eval_set = None
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            eval_set = [(X_val_scaled, y_val)]

        self.regressor.fit(
            X_scaled, y,
            eval_set=eval_set,
        )

        # Training set metrics
        y_pred = self.predict(X)
        mae = float(np.mean(np.abs(y - y_pred)))
        rmse = float(np.sqrt(np.mean((y - y_pred) ** 2)))

        return {"train_mae": round(mae, 3), "train_rmse": round(rmse, 3)}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict quality scores.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            Array of quality scores clipped to [0, 100].
        """
        X_scaled = self.scaler.transform(X)
        scores = self.regressor.predict(X_scaled)
        return np.clip(scores, 0, 100)

    def predict_single(self, X: np.ndarray) -> float:
        """Predict a single quality score."""
        return float(self.predict(X.reshape(1, -1))[0])
