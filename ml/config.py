"""ML pipeline configuration — all hyperparameters and thresholds in one place."""

import os
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KADID_DIR = PROJECT_ROOT / "kadid10k" / "kadid10k"
KADID_IMAGES = KADID_DIR / "images"
KADID_CSV = KADID_DIR / "dmos.csv"

DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
SPLITS_DIR = DATA_DIR / "splits"
SAMPLES_DIR = DATA_DIR / "samples"
RAW_DIR = DATA_DIR / "raw"

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# ── Image processing ───────────────────────────────────────────────────────
IMAGE_RESIZE = (512, 384)  # KADID-10k native resolution
PATCH_SIZE = 64            # For patch-level analysis / heatmaps
NUM_PATCHES_PER_DIM = 8    # 512/64 = 8

# ── KADID-10k distortion → issue mapping ───────────────────────────────────
# Maps KADID distortion type codes to our issue categories
DISTORTION_MAP = {
    # Blur
    "01": "blur",       # Gaussian blur
    "02": "blur",       # Lens blur
    "03": "blur",       # Motion blur
    # Noise
    "11": "noise",      # White noise
    "12": "noise",      # White noise in color
    "13": "noise",      # Impulse noise
    "14": "noise",      # Multiplicative noise
    # Exposure
    "16": "overexposure",   # Brighten
    "17": "underexposure",  # Darken
    # Compression
    "09": "compression_artifact",  # JPEG2000
    "10": "compression_artifact",  # JPEG
    # Contrast
    "25": "low_contrast",          # Contrast change
    # Other → potential defect
    "04": "potential_defect",  # Color diffusion
    "05": "potential_defect",  # Color shift
    "06": "potential_defect",  # Color quantization
    "07": "potential_defect",  # Color saturation 1
    "08": "potential_defect",  # Color saturation 2
    "15": "potential_defect",  # Denoise artifact
    "18": "potential_defect",  # Mean shift
    "19": "potential_defect",  # Jitter
    "20": "potential_defect",  # Non-eccentricity patch
    "21": "potential_defect",  # Pixelate
    "22": "potential_defect",  # Quantization
    "23": "corruption",       # Color block → corruption
    "24": "potential_defect",  # High sharpness
}

# Issue types in canonical order
ISSUE_TYPES = [
    "blur",
    "underexposure",
    "overexposure",
    "noise",
    "compression_artifact",
    "low_contrast",
    "corruption",
    "potential_defect",
]

# ── Severity mapping (KADID severity 01–05, where 05 = worst) ──────────
# KADID severity level → our severity label
SEVERITY_MAP = {
    "01": "low",
    "02": "low",
    "03": "medium",
    "04": "high",
    "05": "high",
}

# ── Quality label thresholds ────────────────────────────────────────────
# DMOS in KADID: 1 (worst) to 5 (best)
# We convert DMOS → quality_score 0–100: score = (dmos - 1) / 4 * 100
QUALITY_LABEL_THRESHOLDS = {
    "DEFECTIVE": 35,      # score < 35
    "DEGRADED": 65,       # 35 <= score < 65
    "ACCEPTABLE": 100,    # score >= 65
}

# ── Feature extraction ──────────────────────────────────────────────────
# Sharpness
LAPLACIAN_KERNEL_SIZE = 3
TENENGRAD_KERNEL_SIZE = 3

# Noise estimation
NOISE_WAVELET = "db2"
NOISE_PATCH_SIZE = 32

# ── Training ────────────────────────────────────────────────────────────
RANDOM_SEED = 42
TEST_SPLIT_RATIO = 0.15
VAL_SPLIT_RATIO = 0.15

# LightGBM defaults
LGBM_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 7,
    "num_leaves": 63,
    "min_child_samples": 20,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
    "verbose": -1,
}

# Isolation Forest for anomaly detection
IFOREST_PARAMS = {
    "n_estimators": 200,
    "contamination": 0.05,
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
}

# ── Model versioning ───────────────────────────────────────────────────
MODEL_VERSION = "1.0.0"

# ── Feature names (set during training, loaded from metadata) ──────────
FEATURE_NAMES: list[str] = []
