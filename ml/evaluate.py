"""Evaluation pipeline — comprehensive metrics and failure analysis.

Evaluates all models on the test set and generates:
- Per-issue precision, recall, F1, ROC-AUC
- Quality score MAE, RMSE, Spearman correlation
- Anomaly detection AUROC
- Confusion matrices
- Calibration curves
- Failure case analysis

Usage:
    python -m ml.evaluate
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    mean_absolute_error,
    mean_squared_error,
)
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ml.config import ARTIFACTS_DIR, SPLITS_DIR, ISSUE_TYPES, FIGURES_DIR, REPORTS_DIR
from ml.features.extractor import FEATURE_ORDER


def load_models():
    """Load all trained models."""
    classifier = joblib.load(ARTIFACTS_DIR / "issue_classifier.joblib")
    regressor = joblib.load(ARTIFACTS_DIR / "quality_regressor.joblib")
    anomaly_detector = joblib.load(ARTIFACTS_DIR / "anomaly_detector.joblib")
    calibrator = joblib.load(ARTIFACTS_DIR / "calibrator.joblib")

    with open(ARTIFACTS_DIR / "metadata.json") as f:
        metadata = json.load(f)

    return classifier, regressor, anomaly_detector, calibrator, metadata


def evaluate_all():
    """Run full evaluation on the test set."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("IMAGE QUALITY ASSESSMENT — EVALUATION")
    print("=" * 60)

    # Load models and test data
    classifier, regressor, anomaly_detector, calibrator, metadata = load_models()

    df_test = pd.read_csv(SPLITS_DIR / "test.csv")
    X_test = df_test[FEATURE_ORDER].values.astype(np.float64)
    print(f"\nTest set: {X_test.shape[0]} samples")

    results = {}

    # ── 1. Issue classification metrics ─────────────────────────────────
    print("\n📊 Issue Classification Metrics:")
    print("-" * 40)

    raw_probas = classifier.predict_proba_all(X_test)
    cal_probas = calibrator.calibrate(raw_probas)
    predictions = classifier.predict(X_test)

    issue_metrics = {}
    all_y_true = []
    all_y_pred = []

    for issue in ISSUE_TYPES:
        col = f"issue_{issue}"
        if col not in df_test.columns:
            continue

        y_true = df_test[col].values
        if y_true.sum() == 0:
            print(f"  {issue}: No positive samples in test set")
            continue

        # Use calibrated probabilities
        y_proba = cal_probas.get(issue, raw_probas.get(issue, np.zeros(len(y_true))))
        y_pred = (y_proba > 0.5).astype(int)

        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        acc = accuracy_score(y_true, y_pred)

        # ROC-AUC (only if both classes present)
        try:
            auc = roc_auc_score(y_true, y_proba)
        except ValueError:
            auc = 0.0

        issue_metrics[issue] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "accuracy": round(acc, 4),
            "roc_auc": round(auc, 4),
            "n_positive": int(y_true.sum()),
            "n_total": int(len(y_true)),
        }

        print(f"  {issue:25s}  P={prec:.3f}  R={rec:.3f}  F1={f1:.3f}  AUC={auc:.3f}")

        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)

        # ROC curve plot
        if auc > 0:
            fpr, tpr, _ = roc_curve(y_true, y_proba)
            plt.figure(figsize=(6, 5))
            plt.plot(fpr, tpr, label=f"AUC = {auc:.3f}")
            plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title(f"ROC Curve — {issue}")
            plt.legend()
            plt.tight_layout()
            plt.savefig(FIGURES_DIR / f"roc_{issue}.png", dpi=150)
            plt.close()

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(5, 4))
        plt.imshow(cm, interpolation="nearest", cmap="Blues")
        plt.title(f"Confusion Matrix — {issue}")
        plt.colorbar()
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(j, i, str(cm[i, j]), ha="center", va="center",
                         color="white" if cm[i, j] > cm.max() / 2 else "black")
        plt.ylabel("True")
        plt.xlabel("Predicted")
        plt.xticks([0, 1], ["No", "Yes"])
        plt.yticks([0, 1], ["No", "Yes"])
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / f"cm_{issue}.png", dpi=150)
        plt.close()

    results["issue_classification"] = issue_metrics

    # ── 2. Quality score regression metrics ─────────────────────────────
    print("\n📈 Quality Score Regression Metrics:")
    print("-" * 40)

    y_true_score = df_test["quality_score"].values
    y_pred_score = regressor.predict(X_test)

    mae = mean_absolute_error(y_true_score, y_pred_score)
    rmse = np.sqrt(mean_squared_error(y_true_score, y_pred_score))
    spearman_r, spearman_p = spearmanr(y_true_score, y_pred_score)

    regression_metrics = {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "spearman_r": round(spearman_r, 4),
        "spearman_p": round(spearman_p, 6),
    }

    print(f"  MAE:  {mae:.3f}")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  Spearman ρ: {spearman_r:.4f} (p={spearman_p:.2e})")

    results["quality_regression"] = regression_metrics

    # Scatter plot
    plt.figure(figsize=(7, 6))
    plt.scatter(y_true_score, y_pred_score, alpha=0.3, s=10)
    plt.plot([0, 100], [0, 100], "r--", alpha=0.5)
    plt.xlabel("True Quality Score")
    plt.ylabel("Predicted Quality Score")
    plt.title(f"Quality Score Prediction (MAE={mae:.2f}, ρ={spearman_r:.3f})")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "quality_scatter.png", dpi=150)
    plt.close()

    # Label accuracy
    y_true_label = df_test["quality_label"].values
    label_map = {True: "DEFECTIVE", False: "other"}

    def score_to_label(s):
        if s < 35:
            return "DEFECTIVE"
        elif s < 65:
            return "DEGRADED"
        else:
            return "ACCEPTABLE"

    y_pred_label = [score_to_label(s) for s in y_pred_score]
    label_acc = accuracy_score(y_true_label, y_pred_label)
    print(f"  Label accuracy: {label_acc:.3f}")
    results["quality_regression"]["label_accuracy"] = round(label_acc, 4)

    # Label confusion matrix
    labels = ["ACCEPTABLE", "DEGRADED", "DEFECTIVE"]
    cm_label = confusion_matrix(y_true_label, y_pred_label, labels=labels)
    plt.figure(figsize=(6, 5))
    plt.imshow(cm_label, interpolation="nearest", cmap="Blues")
    plt.title("Quality Label Confusion Matrix")
    plt.colorbar()
    for i in range(cm_label.shape[0]):
        for j in range(cm_label.shape[1]):
            plt.text(j, i, str(cm_label[i, j]), ha="center", va="center",
                     color="white" if cm_label[i, j] > cm_label.max() / 2 else "black")
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.xticks(range(3), labels, rotation=45)
    plt.yticks(range(3), labels)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "cm_quality_label.png", dpi=150)
    plt.close()

    # ── 3. Anomaly detection metrics ────────────────────────────────────
    print("\n🔍 Anomaly Detection Metrics:")
    print("-" * 40)

    is_anomaly, anomaly_scores = anomaly_detector.predict(X_test)

    # Ground truth: clean=0, distorted=1
    y_true_anom = (1 - df_test["is_clean"].values).astype(int)

    try:
        anom_auc = roc_auc_score(y_true_anom, anomaly_scores)
    except ValueError:
        anom_auc = 0.0

    anom_precision = precision_score(y_true_anom, is_anomaly.astype(int), zero_division=0)
    anom_recall = recall_score(y_true_anom, is_anomaly.astype(int), zero_division=0)

    anomaly_metrics = {
        "auroc": round(anom_auc, 4),
        "precision": round(anom_precision, 4),
        "recall": round(anom_recall, 4),
    }

    print(f"  AUROC: {anom_auc:.4f}")
    print(f"  Precision: {anom_precision:.4f}")
    print(f"  Recall: {anom_recall:.4f}")

    results["anomaly_detection"] = anomaly_metrics

    # ── 4. Feature importance (global) ──────────────────────────────────
    print("\n🌟 Global Feature Importance (Regressor):")
    print("-" * 40)

    importances = regressor.regressor.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    feature_importance = []
    for i in sorted_idx[:10]:
        print(f"  {FEATURE_ORDER[i]:25s}: {importances[i]:.4f}")
        feature_importance.append({
            "feature": FEATURE_ORDER[i],
            "importance": round(float(importances[i]), 4),
        })
    results["feature_importance"] = feature_importance

    # Feature importance bar plot
    plt.figure(figsize=(10, 6))
    plt.barh(range(len(FEATURE_ORDER)),
             [importances[i] for i in sorted_idx],
             tick_label=[FEATURE_ORDER[i] for i in sorted_idx])
    plt.xlabel("Feature Importance")
    plt.title("Global Feature Importance (Quality Regressor)")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "feature_importance.png", dpi=150)
    plt.close()

    # ── 5. Failure analysis ─────────────────────────────────────────────
    print("\n❌ Failure Analysis:")
    print("-" * 40)

    errors = np.abs(y_true_score - y_pred_score)
    worst_idx = np.argsort(errors)[::-1][:20]

    failures = []
    for idx in worst_idx:
        failures.append({
            "filename": df_test.iloc[idx]["filename"],
            "true_score": round(float(y_true_score[idx]), 2),
            "pred_score": round(float(y_pred_score[idx]), 2),
            "error": round(float(errors[idx]), 2),
            "true_label": str(y_true_label[idx]),
            "issue_type": str(df_test.iloc[idx]["issue_type"]),
        })

    print(f"  Top 5 worst predictions:")
    for f in failures[:5]:
        print(f"    {f['filename']}: true={f['true_score']:.1f}, pred={f['pred_score']:.1f}, "
              f"err={f['error']:.1f}, issue={f['issue_type']}")

    results["failure_cases"] = failures

    # ── 6. Save results ─────────────────────────────────────────────────
    results_path = REPORTS_DIR / "evaluation_results.json"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✅ Evaluation complete. Results saved to {results_path}")
    print(f"   Figures saved to {FIGURES_DIR}")

    # ── 7. Generate EVALUATION.md ───────────────────────────────────────
    generate_evaluation_report(results, metadata)

    return results


def generate_evaluation_report(results: dict, metadata: dict):
    """Generate the EVALUATION.md report from results."""
    report_path = REPORTS_DIR / "EVALUATION.md"

    lines = [
        "# Evaluation Report",
        "",
        f"**Model Version:** {metadata.get('model_version', 'N/A')}",
        f"**Training Date:** {metadata.get('training_date', 'N/A')}",
        f"**Training Samples:** {metadata.get('training_samples', 'N/A')}",
        f"**Test Samples:** {metadata.get('test_samples', 'N/A')}",
        "",
        "## Issue Classification Metrics",
        "",
        "| Issue Type | Precision | Recall | F1 | ROC-AUC | # Positive |",
        "|---|---|---|---|---|---|",
    ]

    for issue, m in results.get("issue_classification", {}).items():
        lines.append(
            f"| {issue} | {m['precision']:.3f} | {m['recall']:.3f} | "
            f"{m['f1']:.3f} | {m['roc_auc']:.3f} | {m['n_positive']} |"
        )

    reg = results.get("quality_regression", {})
    lines.extend([
        "",
        "## Quality Score Regression",
        "",
        f"- **MAE:** {reg.get('mae', 'N/A')}",
        f"- **RMSE:** {reg.get('rmse', 'N/A')}",
        f"- **Spearman ρ:** {reg.get('spearman_r', 'N/A')}",
        f"- **Label Accuracy:** {reg.get('label_accuracy', 'N/A')}",
        "",
        "![Quality Score Scatter](figures/quality_scatter.png)",
        "",
        "![Quality Label Confusion Matrix](figures/cm_quality_label.png)",
        "",
        "## Anomaly Detection",
        "",
    ])

    anom = results.get("anomaly_detection", {})
    lines.extend([
        f"- **AUROC:** {anom.get('auroc', 'N/A')}",
        f"- **Precision:** {anom.get('precision', 'N/A')}",
        f"- **Recall:** {anom.get('recall', 'N/A')}",
        "",
        "## Feature Importance",
        "",
        "![Feature Importance](figures/feature_importance.png)",
        "",
        "## Failure Cases",
        "",
        "| Filename | True Score | Predicted | Error | Issue Type |",
        "|---|---|---|---|---|",
    ])

    for f in results.get("failure_cases", [])[:10]:
        lines.append(
            f"| {f['filename']} | {f['true_score']} | {f['pred_score']} | "
            f"{f['error']} | {f['issue_type']} |"
        )

    lines.extend([
        "",
        "## Limitations",
        "",
        "1. **Synthetic data bias**: The model is trained on KADID-10k degradations which are algorithmically generated. Real-world quality issues may differ.",
        "2. **Content dependency**: Quality perception is content-dependent (e.g., noise is more noticeable on smooth areas). Our features partially capture this via patch-level analysis.",
        "3. **Multi-degradation**: Images with multiple simultaneous issues may receive inconsistent predictions since training samples mostly have single degradations.",
        "4. **Resolution sensitivity**: Features are extracted at KADID's native 512×384 resolution. Very different resolutions may shift feature distributions.",
        "5. **Anomaly detector scope**: The Isolation Forest detects deviation from clean image distribution but cannot distinguish between types of anomalies.",
        "",
        "## Baseline Comparison",
        "",
    ])

    baselines = metadata.get("baseline_metrics", {})
    if baselines:
        lines.extend([
            "| Issue Type | Logistic Reg. Acc | Random Forest Acc |",
            "|---|---|---|",
        ])
        for issue, m in baselines.items():
            lines.append(f"| {issue} | {m.get('logistic_regression_acc', 'N/A')} | {m.get('random_forest_acc', 'N/A')} |")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Report saved to {report_path}")


if __name__ == "__main__":
    evaluate_all()
