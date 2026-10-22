"""Training pipeline — trains all models end-to-end.

Orchestrates:
1. Load train/val/test splits
2. Train multi-label issue classifier (LightGBM per issue)
3. Train quality score regressor (LightGBM regression)
4. Train anomaly detector (Isolation Forest on clean images)
5. Calibrate probabilities (isotonic regression on validation set)
6. Save all artifacts with metadata

Usage:
    python -m ml.train
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ml.config import (
    SPLITS_DIR, ARTIFACTS_DIR, ISSUE_TYPES, MODEL_VERSION,
    RANDOM_SEED, LGBM_PARAMS,
)
from ml.features.extractor import FEATURE_ORDER
from ml.models.multilabel_classifier import MultiLabelIssueClassifier
from ml.models.quality_regressor import QualityRegressor
from ml.models.anomaly_detector import AnomalyDetector
from ml.models.calibration import ConfidenceCalibrator


def load_split(split_name: str) -> tuple[np.ndarray, pd.DataFrame]:
    """Load a data split and return (X, df).

    Returns:
        X: Feature matrix (n_samples, n_features).
        df: Full DataFrame with metadata and labels.
    """
    path = SPLITS_DIR / f"{split_name}.csv"
    df = pd.read_csv(path)
    X = df[FEATURE_ORDER].values.astype(np.float64)
    return X, df


def train_all():
    """Train all models and save artifacts."""
    print("=" * 60)
    print("IMAGE QUALITY ASSESSMENT — TRAINING PIPELINE")
    print("=" * 60)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()

    # ── Load data ───────────────────────────────────────────────────────
    print("\n📂 Loading data splits...")
    X_train, df_train = load_split("train")
    X_val, df_val = load_split("val")
    X_test, df_test = load_split("test")

    print(f"  Train: {X_train.shape[0]} samples")
    print(f"  Val:   {X_val.shape[0]} samples")
    print(f"  Test:  {X_test.shape[0]} samples")

    # Issue label columns
    issue_cols = [f"issue_{it}" for it in ISSUE_TYPES]
    y_train_issues = df_train[issue_cols]
    y_val_issues = df_val[issue_cols]

    # Quality scores
    y_train_score = df_train["quality_score"].values
    y_val_score = df_val["quality_score"].values

    # ── 1. Train multi-label classifier ─────────────────────────────────
    print("\n🎯 Training multi-label issue classifier...")
    classifier = MultiLabelIssueClassifier()
    clf_metrics = classifier.fit(X_train, y_train_issues, X_val, y_val_issues)
    print("  Classifier training complete.")

    # ── 2. Train quality regressor ──────────────────────────────────────
    print("\n📊 Training quality score regressor...")
    regressor = QualityRegressor()
    reg_metrics = regressor.fit(X_train, y_train_score, X_val, y_val_score)
    print(f"  Train MAE: {reg_metrics['train_mae']:.3f}")
    print(f"  Train RMSE: {reg_metrics['train_rmse']:.3f}")

    # ── 3. Train anomaly detector ───────────────────────────────────────
    print("\n🔍 Training anomaly detector on clean images...")
    clean_mask = df_train["is_clean"] == 1
    X_clean = X_train[clean_mask]
    print(f"  Clean training samples: {X_clean.shape[0]}")

    anomaly_detector = AnomalyDetector()
    anom_metrics = anomaly_detector.fit(X_clean)
    print(f"  Mean clean score: {anom_metrics['mean_clean_score']:.4f}")

    # ── 4. Calibrate probabilities ──────────────────────────────────────
    print("\n📐 Calibrating probabilities on validation set...")
    val_probas = classifier.predict_proba_all(X_val)
    val_labels = {
        it: df_val[f"issue_{it}"].values for it in ISSUE_TYPES
        if f"issue_{it}" in df_val.columns
    }
    calibrator = ConfidenceCalibrator()
    cal_metrics = calibrator.fit(val_probas, val_labels)
    print(f"  Calibrated {len(cal_metrics)} issue types")
    for it, m in cal_metrics.items():
        print(f"    {it}: ECE = {m['ece']:.4f}")

    # ── 5. Compute reference stats from clean images ────────────────────
    print("\n📈 Computing reference statistics from clean images...")
    clean_features = df_train[df_train["is_clean"] == 1][FEATURE_ORDER]
    ref_stats = {name: float(clean_features[name].median()) for name in FEATURE_ORDER}

    # ── 6. Train baseline models for comparison ─────────────────────────
    print("\n🔄 Training baseline models for comparison...")
    baselines = {}

    # Logistic Regression baseline
    from sklearn.preprocessing import StandardScaler
    scaler_bl = StandardScaler()
    X_train_s = scaler_bl.fit_transform(X_train)
    X_val_s = scaler_bl.transform(X_val)

    for issue in ISSUE_TYPES:
        col = f"issue_{issue}"
        if col not in df_train.columns:
            continue
        y = df_train[col].values
        if y.sum() == 0:
            continue

        # Logistic Regression
        lr = LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced")
        lr.fit(X_train_s, y)
        lr_score = lr.score(X_val_s, df_val[col].values)

        # Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED, class_weight="balanced", n_jobs=-1)
        rf.fit(X_train_s, y)
        rf_score = rf.score(X_val_s, df_val[col].values)

        baselines[issue] = {"logistic_regression_acc": round(lr_score, 4), "random_forest_acc": round(rf_score, 4)}

    print("  Baseline models trained.")

    # ── 7. Save all artifacts ───────────────────────────────────────────
    print("\n💾 Saving model artifacts...")

    joblib.dump(classifier, ARTIFACTS_DIR / "issue_classifier.joblib")
    joblib.dump(regressor, ARTIFACTS_DIR / "quality_regressor.joblib")
    joblib.dump(anomaly_detector, ARTIFACTS_DIR / "anomaly_detector.joblib")
    joblib.dump(calibrator, ARTIFACTS_DIR / "calibrator.joblib")

    elapsed = time.time() - start_time

    # Save metadata
    metadata = {
        "model_version": MODEL_VERSION,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "feature_names": FEATURE_ORDER,
        "num_features": len(FEATURE_ORDER),
        "issue_types": ISSUE_TYPES,
        "training_samples": int(X_train.shape[0]),
        "validation_samples": int(X_val.shape[0]),
        "test_samples": int(X_test.shape[0]),
        "regressor_metrics": reg_metrics,
        "classifier_metrics": clf_metrics,
        "anomaly_metrics": anom_metrics,
        "calibration_metrics": cal_metrics,
        "baseline_metrics": baselines,
        "reference_stats": ref_stats,
        "training_time_seconds": round(elapsed, 1),
        "lgbm_params": LGBM_PARAMS,
        "random_seed": RANDOM_SEED,
    }

    with open(ARTIFACTS_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    # Save reference stats separately for the explanation module
    with open(ARTIFACTS_DIR / "reference_stats.json", "w") as f:
        json.dump(ref_stats, f, indent=2)

    print(f"\n✅ Training complete in {elapsed:.1f}s")
    print(f"   Artifacts saved to: {ARTIFACTS_DIR}")
    print(f"   Model version: {MODEL_VERSION}")

    return metadata


if __name__ == "__main__":
    train_all()
