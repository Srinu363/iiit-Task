"""Build the feature dataset from KADID-10k images.

Reads the KADID-10k CSV, maps distortion types to issue labels,
extracts features from each image, and saves the result as a
feature matrix CSV ready for training.

Usage:
    python -m ml.data.build_dataset
"""

import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.config import (
    KADID_CSV,
    KADID_IMAGES,
    DISTORTION_MAP,
    SEVERITY_MAP,
    ISSUE_TYPES,
    DATA_DIR,
    RANDOM_SEED,
)
from ml.features.extractor import extract_features, FEATURE_ORDER


def parse_kadid_filename(filename: str) -> dict:
    """Parse KADID-10k filename to extract metadata.

    Format: I{ref_id}_{distortion_type}_{severity_level}.png
    Reference images: I{ref_id}.png (no distortion)

    Returns dict with ref_id, distortion_code, severity_code, issue_type, severity_label.
    """
    stem = filename.replace(".png", "")
    parts = stem.split("_")

    if len(parts) == 1:
        # Reference (clean) image
        return {
            "ref_id": parts[0],
            "distortion_code": "00",
            "severity_code": "00",
            "issue_type": "clean",
            "severity_label": "none",
            "is_clean": True,
        }

    return {
        "ref_id": parts[0],
        "distortion_code": parts[1],
        "severity_code": parts[2],
        "issue_type": DISTORTION_MAP.get(parts[1], "unknown"),
        "severity_label": SEVERITY_MAP.get(parts[2], "medium"),
        "is_clean": False,
    }


def dmos_to_quality_score(dmos: float) -> float:
    """Convert KADID DMOS (1=worst, 5=best) to quality score (0-100)."""
    return max(0.0, min(100.0, (dmos - 1.0) / 4.0 * 100.0))


def quality_score_to_label(score: float) -> str:
    """Map quality score to label."""
    if score < 35:
        return "DEFECTIVE"
    elif score < 65:
        return "DEGRADED"
    else:
        return "ACCEPTABLE"


def build_dataset(max_images: int | None = None, output_dir: Path | None = None) -> Path:
    """Build feature dataset from KADID-10k.

    Args:
        max_images: Optional limit for debugging.
        output_dir: Where to save the CSV. Defaults to data/.

    Returns:
        Path to the generated CSV file.
    """
    if output_dir is None:
        output_dir = DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features.csv"

    # Read KADID CSV
    with open(KADID_CSV, "r") as f:
        reader = csv.DictReader(f)
        kadid_rows = list(reader)

    print(f"KADID-10k: {len(kadid_rows)} distorted images")

    # Build list of all images to process
    images_to_process = []

    # Add reference (clean) images with DMOS=5.0 (perfect quality)
    ref_images = set()
    for row in kadid_rows:
        ref_images.add(row["ref_img"])

    for ref_img in sorted(ref_images):
        img_path = str(KADID_IMAGES / ref_img)
        if os.path.exists(img_path):
            images_to_process.append({
                "filename": ref_img,
                "path": img_path,
                "dmos": 5.0,
                "dmos_var": 0.0,
                **parse_kadid_filename(ref_img),
            })

    # Add distorted images
    for row in kadid_rows:
        img_path = str(KADID_IMAGES / row["dist_img"])
        if os.path.exists(img_path):
            meta = parse_kadid_filename(row["dist_img"])
            images_to_process.append({
                "filename": row["dist_img"],
                "path": img_path,
                "dmos": float(row["dmos"]),
                "dmos_var": float(row["var"]),
                **meta,
            })

    if max_images:
        images_to_process = images_to_process[:max_images]

    print(f"Processing {len(images_to_process)} images...")

    # Build header
    header = (
        ["filename", "ref_id", "distortion_code", "severity_code",
         "issue_type", "severity_label", "is_clean", "dmos", "dmos_var",
         "quality_score", "quality_label"]
        + FEATURE_ORDER
        + [f"issue_{it}" for it in ISSUE_TYPES]
    )

    # Process images and extract features
    rows_out = []
    errors = []
    start_time = time.time()

    for item in tqdm(images_to_process, desc="Extracting features"):
        try:
            features = extract_features(item["path"])
            quality_score = dmos_to_quality_score(item["dmos"])
            quality_label = quality_score_to_label(quality_score)

            # Binary issue labels (one-hot for the detected issue type)
            issue_labels = {f"issue_{it}": 0 for it in ISSUE_TYPES}
            if not item["is_clean"] and item["issue_type"] in ISSUE_TYPES:
                issue_labels[f"issue_{item['issue_type']}"] = 1

            row = {
                "filename": item["filename"],
                "ref_id": item["ref_id"],
                "distortion_code": item["distortion_code"],
                "severity_code": item["severity_code"],
                "issue_type": item["issue_type"],
                "severity_label": item["severity_label"],
                "is_clean": int(item["is_clean"]),
                "dmos": item["dmos"],
                "dmos_var": item["dmos_var"],
                "quality_score": round(quality_score, 2),
                "quality_label": quality_label,
            }
            row.update(features)
            row.update(issue_labels)
            rows_out.append(row)
        except Exception as e:
            errors.append((item["filename"], str(e)))

    elapsed = time.time() - start_time
    print(f"\nExtracted features from {len(rows_out)} images in {elapsed:.1f}s")
    if errors:
        print(f"Errors ({len(errors)}):")
        for fn, err in errors[:10]:
            print(f"  {fn}: {err}")

    # Save CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Saved features to {output_path}")

    # Save data hash for reproducibility
    data_hash = hashlib.sha256(open(output_path, "rb").read()).hexdigest()[:16]
    meta = {
        "num_images": len(rows_out),
        "num_features": len(FEATURE_ORDER),
        "feature_names": FEATURE_ORDER,
        "num_errors": len(errors),
        "data_hash": data_hash,
        "elapsed_seconds": round(elapsed, 1),
    }
    meta_path = output_dir / "dataset_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Dataset hash: {data_hash}")

    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build feature dataset from KADID-10k")
    parser.add_argument("--max-images", type=int, default=None, help="Limit images for debugging")
    args = parser.parse_args()
    build_dataset(max_images=args.max_images)
