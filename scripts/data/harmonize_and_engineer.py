"""Prepare linked observations for the Preliminary duration experiment.

Based on Kien's feature pipeline. Each row remains a Zenodo OR activity episode;
no patient, staffing or clinical features are joined from unrelated populations.
This prepares data only; it does not implement a runtime L3 estimator.
"""
import argparse
import json
from pathlib import Path

import pandas as pd


FEATURE_COLUMNS = ["nurseflow_task_type", "task_name", "task_category"]
TARGET_COLUMN = "actual_duration_min"
GROUP_COLUMN = "staff_id"


def validate_activity_features(features, episodes):
    """Reject mixed processing runs before an EDA or holdout uses their rows."""
    columns = [
        "episode_id", "staff_id", "date", "source_excel_rows",
        *FEATURE_COLUMNS, "episode_duration_min",
    ]
    expected = episodes.loc[episodes["nurseflow_task_type"] != "break", columns]
    expected = expected.rename(columns={"episode_duration_min": TARGET_COLUMN})
    expected = expected.sort_values("episode_id").reset_index(drop=True)
    observed = features[expected.columns].sort_values("episode_id").reset_index(drop=True)
    if not features["episode_id"].is_unique or not expected.equals(observed):
        raise ValueError("Feature rows and source episodes differ; regenerate both tables")


def build_harmonized_datasets(proc_dir: Path) -> dict:
    """Export non-break activity episodes with source lineage and a minimal feature set."""
    episodes = pd.read_csv(proc_dir / "zenodo_task_episodes_en.csv")
    columns = [
        "episode_id", "staff_id", "date", "source_excel_rows",
        *FEATURE_COLUMNS, "episode_duration_min",
    ]
    features = episodes.loc[episodes["nurseflow_task_type"] != "break", columns].copy()
    features = features.rename(columns={"episode_duration_min": TARGET_COLUMN})
    features["target_kind"] = "observed_activity_episode"
    features["source_dataset"] = "zenodo:20754938"
    if (features[TARGET_COLUMN] <= 0).any():
        raise ValueError("Activity duration must be positive")
    if features[FEATURE_COLUMNS + [TARGET_COLUMN, GROUP_COLUMN]].isna().any().any():
        raise ValueError("Missing linked feature, target or staff group")
    output = proc_dir / "l3_activity_features.csv"
    features.to_csv(output, index=False, lineterminator="\n")
    lookup = features.groupby(FEATURE_COLUMNS, sort=True)[TARGET_COLUMN].agg(
        episodes="count", median_duration_min="median"
    ).reset_index()
    lookup["target_kind"] = "observed_activity_episode"
    lookup["source_dataset"] = "zenodo:20754938"
    lookup.to_csv(proc_dir / "activity_duration_lookup.csv", index=False, lineterminator="\n")
    return {
        "rows": len(features), "staff_groups": int(features[GROUP_COLUMN].nunique()),
        "features": FEATURE_COLUMNS, "target": TARGET_COLUMN,
        "target_kind": "observed_activity_episode", "output": str(output),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proc-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    print(json.dumps(build_harmonized_datasets(args.proc_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
