"""SHAP-based feature importance for model predictions.

Computes SHAP values using TreeExplainer for LightGBM models,
providing both global and per-prediction feature importance.
"""

import numpy as np


def compute_shap_values(model, X: np.ndarray, feature_names: list[str]) -> dict:
    """Compute SHAP values for predictions.

    Uses TreeExplainer for efficient exact SHAP computation on
    tree-based models (LightGBM).

    Args:
        model: Trained LightGBM model (classifier or regressor).
        X: Feature matrix (n_samples, n_features), already scaled.
        feature_names: List of feature names.

    Returns:
        Dict with shap_values array and feature_names.
    """
    import shap

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # For binary classifiers, shap_values may be a list [class_0, class_1]
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # Use class 1 (positive) SHAP values

    return {
        "shap_values": shap_values,
        "feature_names": feature_names,
        "expected_value": float(explainer.expected_value[1])
        if isinstance(explainer.expected_value, (list, np.ndarray))
        else float(explainer.expected_value),
    }


def get_top_features(shap_values: np.ndarray, feature_names: list[str],
                     feature_values: np.ndarray, top_k: int = 5) -> list[dict]:
    """Get the top-K most important features for a single prediction.

    Args:
        shap_values: SHAP values for one sample (n_features,).
        feature_names: Feature names.
        feature_values: Raw feature values for this sample (n_features,).
        top_k: Number of top features to return.

    Returns:
        List of dicts with feature name, SHAP value, raw value, and direction.
    """
    abs_shap = np.abs(shap_values)
    top_indices = np.argsort(abs_shap)[::-1][:top_k]

    features = []
    for idx in top_indices:
        features.append({
            "feature": feature_names[idx],
            "shap_value": round(float(shap_values[idx]), 4),
            "raw_value": round(float(feature_values[idx]), 4),
            "direction": "increases_risk" if shap_values[idx] > 0 else "decreases_risk",
        })

    return features


def global_feature_importance(shap_values: np.ndarray,
                               feature_names: list[str]) -> list[dict]:
    """Compute global feature importance from SHAP values.

    Args:
        shap_values: SHAP values matrix (n_samples, n_features).
        feature_names: Feature names.

    Returns:
        List of features sorted by mean absolute SHAP value.
    """
    mean_abs = np.mean(np.abs(shap_values), axis=0)
    indices = np.argsort(mean_abs)[::-1]

    return [
        {
            "feature": feature_names[i],
            "importance": round(float(mean_abs[i]), 4),
        }
        for i in indices
    ]
