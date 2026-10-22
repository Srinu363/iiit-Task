# Technical Report: Image Quality & Defect Detection

## 1. Problem Formulation

Given an input image, the system must:
1. **Score** overall quality on a 0–100 scale
2. **Classify** quality as ACCEPTABLE / DEGRADED / DEFECTIVE
3. **Detect** specific issues: blur, underexposure, overexposure, noise, compression artifacts, low contrast, corruption, and potential visual defects
4. **Explain** decisions with interpretable features and spatial heatmaps

## 2. Dataset: KADID-10k

We use the **Konstanz Artificially Distorted Image quality Database (KADID-10k)**:
- 81 pristine reference images (512×384 RGB)
- 10,125 distorted images = 81 refs × 25 distortion types × 5 severity levels
- DMOS scores (1–5 scale, higher = better) from subjective quality assessment
- 25 distortion types mapped to our 8 issue categories

### Distortion-to-Issue Mapping

| Distortion Code | KADID Type | Our Issue Category |
|---|---|---|
| 01–03 | Gaussian/Lens/Motion blur | blur |
| 11–14 | White/Color/Impulse/Multiplicative noise | noise |
| 16 | Brighten | overexposure |
| 17 | Darken | underexposure |
| 09–10 | JPEG2000/JPEG compression | compression_artifact |
| 25 | Contrast change | low_contrast |
| 23 | Color block | corruption |
| 04–08, 15, 18–22, 24 | Various color/spatial/denoise | potential_defect |

### Data Split Strategy

- **Grouped by source image**: All distortions of the same reference image stay in the same split
- **Split ratios**: 70% train / 15% validation / 15% test
- **No data leakage**: The model never sees distortions of a test reference image during training

## 3. Feature Engineering

We extract 23 features across 5 categories:

### Sharpness (3 features)
- **Laplacian variance**: Second-derivative response magnitude. Blurred images produce low variance.
- **Tenengrad**: Mean squared Sobel gradient magnitude. More robust to noise than Laplacian.
- **FFT high-frequency ratio**: Fraction of spectral energy above the median frequency. Blur removes high-frequency content.

### Exposure (8 features)
- **Luminance mean/median/std**: Basic brightness statistics.
- **Dark/bright clip percentage**: Fraction of pixels crushed to near-black or near-white.
- **Luminance entropy**: Information content of the histogram. Low entropy = narrow intensity range.
- **Dynamic range**: Effective range between 1st and 99th percentile.
- **Luminance skewness**: Positive = dark-biased, negative = bright-biased.

### Noise (3 features)
- **Immerkaer estimator**: Robust noise σ from a specific Laplacian kernel that suppresses image structure.
- **Wavelet MAD**: Median absolute deviation of finest-scale diagonal wavelet coefficients (HH subband).
- **Flat-patch variance**: Average variance in the smoothest (lowest-gradient) image patches.

### Contrast & Color (5 features)
- **RMS contrast**: Standard deviation of luminance. Low = flat/washed-out image.
- **Michelson contrast**: (Imax-Imin)/(Imax+Imin) using 1st/99th percentiles.
- **Colorfulness**: Hasler & Süsstrunk metric on opponent channels.
- **Saturation mean/std**: HSV saturation channel statistics.

### Artifacts & Texture (4 features)
- **Blockiness**: Ratio of pixel differences at 8×8 block boundaries vs. non-boundaries. High = JPEG artifacts.
- **Edge density**: Fraction of Canny edge pixels. Very low = blur; very high = noise.
- **Spatial entropy**: Mean local entropy over disk neighborhoods.
- **LBP uniformity**: Uniformity of Local Binary Pattern histogram. Regular texture = high uniformity.

## 4. Model Architecture

### Hybrid Approach

We use a **hybrid pipeline** combining engineered features with learned models:

1. **Quality Score Regressor** (LightGBM regression): Predicts 0–100 quality score from 23 features
2. **Multi-label Issue Classifier** (LightGBM binary × 8): One binary classifier per issue type, with class-weight balancing
3. **Anomaly Detector** (Isolation Forest): Trained only on clean reference images; flags images whose features deviate from the clean distribution
4. **Probability Calibrator** (Isotonic Regression): Calibrates raw classifier probabilities on the validation set

### Why LightGBM?

- **Interpretable**: Tree-based features importances and SHAP values provide clear explanations
- **Fast inference**: Sub-millisecond prediction for 23 features
- **Handles feature scale differences**: No normalization issues across vastly different feature scales
- **Gradient boosting is state-of-the-art** for tabular/engineered features
- **Small model size**: Serialized models are under 5MB total

### Why Not Deep Learning?

We considered MobileNetV3 as a feature extractor, but:
- Our engineered features are **domain-specific and interpretable**, directly measuring blur, noise, exposure, etc.
- Transfer learning would add model complexity without measurably improving results on this task
- The KADID-10k distortions are well-captured by classical CV features
- Inference would be 10–100× slower
- Explainability would require Grad-CAM instead of simple SHAP values

## 5. Training Procedure

1. Extract 23 features from all 10,206 images (81 clean + 10,125 distorted)
2. Convert DMOS (1–5) to quality score (0–100): `score = (dmos - 1) / 4 * 100`
3. Group-split by source image into train/val/test
4. Train regressor with early stopping on validation MAE
5. Train 8 binary classifiers with `scale_pos_weight` for class imbalance
6. Train Isolation Forest on clean images only
7. Calibrate probabilities using isotonic regression on validation predictions
8. Save all artifacts with metadata (version, metrics, feature names, data hash)

## 6. Explainability

- **SHAP values**: Per-prediction feature importance showing which features drove the decision
- **Human-readable explanations**: Feature values compared to clean-image medians (e.g., "Laplacian variance 12.4, well below the sharp-image median of 310")
- **Patch-level heatmaps**: The image is divided into 64×64 patches, and sharpness/noise/brightness/contrast are computed per-patch, producing spatial quality maps
- **Uncertainty flags**: Predictions near the decision boundary (±15% confidence) are flagged as "uncertain"

## 7. Limitations

1. **Synthetic distortion bias**: KADID-10k uses algorithmic degradations. Real-world quality issues (motion blur from camera shake, sensor noise patterns) may differ.
2. **Single distortion per image**: Training images have one distortion type each. Images with multiple co-occurring issues may receive inconsistent predictions.
3. **Resolution dependency**: Features are calibrated for 512×384 images. Very different resolutions shift feature distributions.
4. **Content dependency**: Quality perception varies by content (noise is more visible on smooth areas). Our features partially address this via patch-level analysis.
5. **Anomaly detector generalization**: The Isolation Forest detects deviation from clean-image features but cannot distinguish between types of novel anomalies.
