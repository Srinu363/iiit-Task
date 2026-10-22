# ML Pipeline

## Overview

The ML pipeline extracts 23 computer vision features from images and uses gradient-boosted models to predict quality scores and detect specific issues.

## Components

### Feature Extraction (`features/`)
- `sharpness.py` — Laplacian variance, Tenengrad, FFT high-frequency ratio
- `exposure.py` — Luminance statistics, histogram clipping, entropy, dynamic range
- `noise.py` — Immerkaer estimator, wavelet MAD, flat-patch variance
- `contrast_color.py` — RMS/Michelson contrast, colorfulness, saturation
- `artifacts.py` — Blockiness, edge density, spatial entropy, LBP uniformity
- `extractor.py` — Combines all modules into a fixed-order feature vector

### Models (`models/`)
- `multilabel_classifier.py` — One LightGBM binary classifier per issue type
- `quality_regressor.py` — LightGBM regression for 0-100 quality score
- `anomaly_detector.py` — Isolation Forest trained on clean images
- `calibration.py` — Isotonic regression probability calibration

### Explainability (`explain/`)
- `feature_importance.py` — SHAP values for per-prediction explanations
- `heatmaps.py` — Patch-level quality heatmaps
- `reasons.py` — Human-readable quality explanations

### Data (`data/`)
- `build_dataset.py` — Feature extraction from KADID-10k
- `split.py` — Grouped train/val/test split by source image

### Training & Evaluation
- `train.py` — Full training pipeline
- `evaluate.py` — Metrics, plots, and failure analysis
- `predict.py` — Inference pipeline for the backend

## Usage

```bash
# From project root:
python -m ml.data.build_dataset   # Extract features
python -m ml.data.split            # Split data
python -m ml.train                 # Train models
python -m ml.evaluate              # Evaluate
```

## Artifacts

After training, `artifacts/` contains:
- `issue_classifier.joblib` — Multi-label classifier
- `quality_regressor.joblib` — Quality score regressor
- `anomaly_detector.joblib` — Anomaly detector
- `calibrator.joblib` — Probability calibrator
- `metadata.json` — Model version, metrics, feature names, training info
- `reference_stats.json` — Clean image feature medians
