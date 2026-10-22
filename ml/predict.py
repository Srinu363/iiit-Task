"""Inference pipeline — used by the backend for single-image prediction.

Loads trained models once and provides a simple predict() interface
that returns quality score, label, detected issues, explanations,
and heatmap data.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import ARTIFACTS_DIR, ISSUE_TYPES
from ml.features.extractor import (
    FEATURE_ORDER,
    extract_features_from_arrays,
    features_to_vector,
    load_and_preprocess,
)
from ml.explain.heatmaps import compute_patch_heatmaps
from ml.explain.reasons import generate_explanations, set_reference_stats


class QualityPredictor:
    """Singleton inference pipeline that loads models once and predicts.

    Usage:
        predictor = QualityPredictor.load(artifacts_dir)
        result = predictor.predict_from_path("/path/to/image.jpg")
    """

    def __init__(self, classifier, regressor, anomaly_detector, calibrator,
                 metadata: dict, ref_stats: dict):
        self.classifier = classifier
        self.regressor = regressor
        self.anomaly_detector = anomaly_detector
        self.calibrator = calibrator
        self.metadata = metadata
        self.ref_stats = ref_stats
        set_reference_stats(ref_stats)

    @classmethod
    def load(cls, artifacts_dir: str | Path | None = None) -> "QualityPredictor":
        """Load all model artifacts from disk.

        Args:
            artifacts_dir: Path to the artifacts directory.
                          Defaults to ml/artifacts/.

        Returns:
            Initialized QualityPredictor instance.
        """
        if artifacts_dir is None:
            artifacts_dir = ARTIFACTS_DIR
        artifacts_dir = Path(artifacts_dir)

        classifier = joblib.load(artifacts_dir / "issue_classifier.joblib")
        regressor = joblib.load(artifacts_dir / "quality_regressor.joblib")
        anomaly_detector = joblib.load(artifacts_dir / "anomaly_detector.joblib")
        calibrator = joblib.load(artifacts_dir / "calibrator.joblib")

        with open(artifacts_dir / "metadata.json") as f:
            metadata = json.load(f)

        ref_stats_path = artifacts_dir / "reference_stats.json"
        if ref_stats_path.exists():
            with open(ref_stats_path) as f:
                ref_stats = json.load(f)
        else:
            ref_stats = {}

        return cls(classifier, regressor, anomaly_detector, calibrator,
                   metadata, ref_stats)

    def predict_from_path(self, image_path: str, generate_heatmaps: bool = True) -> dict[str, Any]:
        """Run full prediction pipeline on an image file.

        Args:
            image_path: Path to the image.
            generate_heatmaps: Whether to compute patch-level heatmaps.

        Returns:
            Complete analysis result dict.
        """
        start = time.time()
        gray, bgr = load_and_preprocess(image_path)
        return self._predict_from_arrays(gray, bgr, generate_heatmaps, start)

    def predict_from_bytes(self, image_bytes: bytes, generate_heatmaps: bool = True) -> dict[str, Any]:
        """Run prediction on raw image bytes.

        Args:
            image_bytes: Raw image file bytes.
            generate_heatmaps: Whether to compute patch-level heatmaps.

        Returns:
            Complete analysis result dict.
        """
        start = time.time()
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Cannot decode image from bytes")
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        return self._predict_from_arrays(gray, bgr, generate_heatmaps, start)

    def _predict_from_arrays(self, gray: np.ndarray, bgr: np.ndarray,
                              generate_heatmaps: bool, start_time: float) -> dict[str, Any]:
        """Core prediction logic."""
        # Extract features
        features = extract_features_from_arrays(gray, bgr)
        feature_vector = features_to_vector(features).reshape(1, -1)

        # Quality score
        quality_score = float(self.regressor.predict(feature_vector)[0])
        quality_score = round(max(0, min(100, quality_score)), 1)

        # Quality label
        if quality_score < 35:
            quality_label = "DEFECTIVE"
        elif quality_score < 65:
            quality_label = "DEGRADED"
        else:
            quality_label = "ACCEPTABLE"

        # Issue detection
        raw_probas = self.classifier.predict_proba_all(feature_vector)
        cal_probas = self.calibrator.calibrate(raw_probas)

        issues = []
        for issue_type in ISSUE_TYPES:
            if issue_type not in cal_probas:
                continue
            confidence = float(cal_probas[issue_type][0])
            if confidence > 0.5:
                if confidence > 0.85:
                    severity = "high"
                elif confidence > 0.65:
                    severity = "medium"
                else:
                    severity = "low"

                uncertain = self.calibrator.is_uncertain(confidence)
                issues.append({
                    "type": issue_type,
                    "severity": severity,
                    "confidence": round(confidence, 3),
                    "uncertain": uncertain,
                })

        issues.sort(key=lambda x: x["confidence"], reverse=True)

        # Anomaly detection
        is_anomaly, anomaly_score = self.anomaly_detector.predict_single(feature_vector[0])
        if is_anomaly and anomaly_score > 0.6:
            # Check if "potential_defect" isn't already in issues
            has_defect = any(i["type"] == "potential_defect" for i in issues)
            if not has_defect:
                issues.append({
                    "type": "potential_defect",
                    "severity": "medium" if anomaly_score < 0.8 else "high",
                    "confidence": round(anomaly_score, 3),
                    "uncertain": False,
                })

        # Explanations
        explanations = generate_explanations(features, issues, quality_score, self.ref_stats)

        # Feature importance for this prediction
        top_features = []
        for name in FEATURE_ORDER:
            ref = self.ref_stats.get(name, 0)
            if ref != 0:
                deviation = abs(features[name] - ref) / max(abs(ref), 1e-10)
            else:
                deviation = abs(features[name])
            top_features.append({
                "feature": name,
                "value": round(features[name], 4),
                "reference": round(ref, 4),
                "deviation": round(deviation, 4),
            })
        top_features.sort(key=lambda x: x["deviation"], reverse=True)

        # Heatmaps
        heatmap_data = None
        if generate_heatmaps:
            patch_heatmaps = compute_patch_heatmaps(gray, patch_size=64)
            heatmap_data = {}
            for name, hm in patch_heatmaps.items():
                heatmap_data[name] = hm.tolist()

        latency_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "quality_score": quality_score,
            "quality_label": quality_label,
            "issues": issues,
            "image_stats": {
                "width": bgr.shape[1],
                "height": bgr.shape[0],
                "channels": bgr.shape[2],
                **{k: round(v, 4) for k, v in features.items()},
            },
            "explanations": explanations,
            "feature_importance": top_features[:10],
            "heatmaps": heatmap_data,
            "anomaly_score": round(float(anomaly_score) if isinstance(anomaly_score, (float, np.floating)) else anomaly_score, 3),
            "model_version": self.metadata.get("model_version", "unknown"),
            "latency_ms": latency_ms,
        }

    def get_model_info(self) -> dict:
        """Return model metadata for the /model-info endpoint."""
        return {
            "model_version": self.metadata.get("model_version"),
            "training_date": self.metadata.get("training_date"),
            "num_features": self.metadata.get("num_features"),
            "feature_names": self.metadata.get("feature_names"),
            "issue_types": self.metadata.get("issue_types"),
            "training_samples": self.metadata.get("training_samples"),
            "regressor_metrics": self.metadata.get("regressor_metrics"),
        }
