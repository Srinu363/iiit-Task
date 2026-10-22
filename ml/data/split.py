"""Split dataset into train/val/test with grouped splitting by source image.

Groups by ref_id so that all distortions of the same source image
stay in the same split — this prevents data leakage where the model
memorises image content rather than quality features.

Usage:
    python -m ml.data.split
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.config import DATA_DIR, SPLITS_DIR, RANDOM_SEED, TEST_SPLIT_RATIO, VAL_SPLIT_RATIO


def create_splits(features_csv: Path | None = None, output_dir: Path | None = None) -> dict[str, Path]:
    """Create grouped train/val/test splits.

    Args:
        features_csv: Path to features.csv. Defaults to data/features.csv.
        output_dir: Where to save split CSVs. Defaults to data/splits/.

    Returns:
        Dict mapping split name to CSV path.
    """
    if features_csv is None:
        features_csv = DATA_DIR / "features.csv"
    if output_dir is None:
        output_dir = SPLITS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(features_csv)
    print(f"Total samples: {len(df)}")
    print(f"Unique source images: {df['ref_id'].nunique()}")

    groups = df["ref_id"].values

    # First split: separate test set
    gss_test = GroupShuffleSplit(
        n_splits=1,
        test_size=TEST_SPLIT_RATIO,
        random_state=RANDOM_SEED,
    )
    train_val_idx, test_idx = next(gss_test.split(df, groups=groups))

    df_test = df.iloc[test_idx]
    df_train_val = df.iloc[train_val_idx]

    # Second split: separate validation from training
    val_ratio_adjusted = VAL_SPLIT_RATIO / (1 - TEST_SPLIT_RATIO)
    groups_tv = df_train_val["ref_id"].values
    gss_val = GroupShuffleSplit(
        n_splits=1,
        test_size=val_ratio_adjusted,
        random_state=RANDOM_SEED,
    )
    train_idx, val_idx = next(gss_val.split(df_train_val, groups=groups_tv))

    df_train = df_train_val.iloc[train_idx]
    df_val = df_train_val.iloc[val_idx]

    # Save splits
    paths = {}
    for name, split_df in [("train", df_train), ("val", df_val), ("test", df_test)]:
        path = output_dir / f"{name}.csv"
        split_df.to_csv(path, index=False)
        paths[name] = path

        # Print split stats
        n_clean = split_df["is_clean"].sum()
        n_dist = len(split_df) - n_clean
        ref_ids = split_df["ref_id"].unique()
        print(f"\n{name.upper()}: {len(split_df)} samples "
              f"({n_clean} clean, {n_dist} distorted), "
              f"{len(ref_ids)} source images")
        print(f"  Source images: {sorted(ref_ids)[:5]}...")
        print(f"  Quality labels: {split_df['quality_label'].value_counts().to_dict()}")

    # Verify no source image overlap
    train_refs = set(df_train["ref_id"].unique())
    val_refs = set(df_val["ref_id"].unique())
    test_refs = set(df_test["ref_id"].unique())

    assert train_refs.isdisjoint(val_refs), "Train/Val overlap!"
    assert train_refs.isdisjoint(test_refs), "Train/Test overlap!"
    assert val_refs.isdisjoint(test_refs), "Val/Test overlap!"
    print("\n[OK] No source image overlap between splits (no data leakage)")

    return paths


if __name__ == "__main__":
    create_splits()
