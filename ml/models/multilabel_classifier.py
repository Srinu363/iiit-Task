"""Multi-label classifier for issue detection.

Trains one binary classifier per issue type using LightGBM.
Each classifier predicts whether a specific issue is present
and outputs a calibrated probability as confidence.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.config import LGBM_PARAMS, ISSUE_TYPES
from ml.features.extractor import FEATURE_ORDER


class MultiLabelIssueClassifier:
    """One-vs-rest binary classifiers for each issue type.

    Each issue type gets its own LightGBM binary classifier trained
    on the same feature set. This allows independent detection of
    multiple co-occurring issues.
    """

    def __init__(self, lgbm_params: dict | None = None):
        self.params = lgbm_params or LGBM_PARAMS.copy()
        self.classifiers: dict[str, LGBMClassifier] = {}
        self.scaler = StandardScaler()
        self.issue_types = ISSUE_TYPES
        self.feature_names = FEATURE_ORDER

    def fit(self, X: np.ndarray, y_multi: pd.DataFrame,
            X_val: np.ndarray | None = None,
            y_val_multi: pd.DataFrame | None = None) -> dict[str, dict]:
        """Train a binary classifier for each issue type.

        Args:
            X: Feature matrix (n_samples, n_features).
            y_multi: DataFrame with columns issue_{type} (binary labels).
            X_val: Optional validation features for early stopping.
            y_val_multi: Optional validation labels.

        Returns:
            Dict of training metrics per issue type.
        """
        X_scaled = self.scaler.fit_transform(X)
        X_val_scaled = self.scaler.transform(X_val) if X_val is not None else None

        metrics = {}
        for issue in self.issue_types:
            col = f"issue_{issue}"
            if col not in y_multi.columns:
                print(f"  Skipping {issue}: no label column")
                continue

            y = y_multi[col].values
            n_pos = y.sum()
            n_neg = len(y) - n_pos

            if n_pos == 0:
                print(f"  Skipping {issue}: no positive samples")
                continue

            print(f"  Training {issue} classifier ({n_pos} pos / {n_neg} neg)...")

            # Adjust scale_pos_weight for class imbalance
            params = self.params.copy()
            params["scale_pos_weight"] = max(1.0, n_neg / max(n_pos, 1))

            clf = LGBMClassifier(**params)

            eval_set = None
            callbacks = None
            if X_val_scaled is not None and y_val_multi is not None:
                y_val = y_val_multi[col].values
                eval_set = [(X_val_scaled, y_val)]
                callbacks = [lambda env: None]  # Suppress verbose output

            clf.fit(
                X_scaled, y,
                eval_set=eval_set,
            )

            self.classifiers[issue] = clf
            metrics[issue] = {
                "n_positive": int(n_pos),
                "n_negative": int(n_neg),
                "scale_pos_weight": params["scale_pos_weight"],
            }

        return metrics

    def predict(self, X: np.ndarray) -> list[dict]:
        """Predict issues for each sample.

        Args:
            X: Feature matrix (n_samples, n_features).

        Returns:
            List of dicts, each containing detected issues with confidence.
        """
        X_scaled = self.scaler.transform(X)
        results = []

        for i in range(X_scaled.shape[0]):
            issues = []
            x = X_scaled[i:i + 1]

            for issue_type, clf in self.classifiers.items():
                proba = clf.predict_proba(x)[0]
                # proba is [prob_negative, prob_positive]
                confidence = float(proba[1]) if len(proba) > 1 else float(proba[0])

                if confidence > 0.5:
                    # Determine severity from confidence
                    if confidence > 0.85:
                        severity = "high"
                    elif confidence > 0.65:
                        severity = "medium"
                    else:
                        severity = "low"

                    issues.append({
                        "type": issue_type,
                        "severity": severity,
                        "confidence": round(confidence, 3),
                    })

            # Sort by confidence descending
            issues.sort(key=lambda x: x["confidence"], reverse=True)
            results.append(issues)

        return results

    def predict_proba_all(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """Get probability predictions for all issue types.

        Returns:
            Dict mapping issue_type → array of probabilities (n_samples,).
        """
        X_scaled = self.scaler.transform(X)
        probas = {}
        for issue_type, clf in self.classifiers.items():
            p = clf.predict_proba(X_scaled)
            probas[issue_type] = p[:, 1] if p.shape[1] > 1 else p[:, 0]
        return probas
