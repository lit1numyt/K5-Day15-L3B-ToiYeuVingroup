"""Compare three fixed OR-duration alternatives and a later-time holdout.

This is an exploratory extension of the Preliminary experiment. Its target is
the same reconstructed OR episode duration. It does not fit a ward estimator.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from run_eda import FEATURE_COLUMNS, metrics
from harmonize_and_engineer import validate_activity_features


def predict_options(train, test):
    """Fit every statistic/encoder on training rows only, with fixed settings."""
    target = train["actual_duration_min"]
    activity = test["task_name"]
    medians = train.groupby("task_name")["actual_duration_min"].median()
    activity_median = activity.map(medians)
    type_medians = train.groupby("nurseflow_task_type")["actual_duration_min"].median()
    type_fallback = test["nurseflow_task_type"].map(type_medians).fillna(target.median())
    predictions = {
        "activity_median": activity_median.fillna(target.median()).to_numpy(),
        "activity_mean": activity.map(
            train.groupby("task_name")["actual_duration_min"].mean()
        ).fillna(target.mean()).to_numpy(),
        "hierarchical_median": activity_median.fillna(type_fallback).to_numpy(),
    }
    # Match the previous GBT settings; vary only the stated features/target/loss.
    for name, columns, loss, log_target in [
        ("gradient_boosting", FEATURE_COLUMNS, "squared_error", False),
        ("gb_absolute_name", ["task_name"], "absolute_error", False),
        ("gb_log_name", ["task_name"], "squared_error", True),
    ]:
        model = make_pipeline(
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            GradientBoostingRegressor(
                n_estimators=180, max_depth=4, learning_rate=0.05,
                random_state=42, loss=loss,
            ),
        )
        model.fit(train[columns], np.log1p(target) if log_target else target)
        prediction = model.predict(test[columns])
        if log_target:
            prediction = np.expm1(prediction)
        predictions[name] = np.maximum(prediction, 0.01)
    return predictions


def compare_options(proc_dir, output_dir):
    features_path = proc_dir / "l3_activity_features.csv"
    episodes_path = proc_dir / "zenodo_task_episodes_en.csv"
    features = pd.read_csv(features_path)
    episodes = pd.read_csv(episodes_path)
    validate_activity_features(features, episodes)
    df = features.merge(episodes[[
        "episode_id", "episode_start_min_from_date", "episode_end_min_from_date"
    ]], on="episode_id", validate="one_to_one")
    elapsed = df["episode_end_min_from_date"] - df["episode_start_min_from_date"]
    if not df["actual_duration_min"].gt(0).all() or not np.allclose(elapsed, df["actual_duration_min"]):
        raise ValueError("Feature duration differs from the source episode interval")
    splitter = GroupKFold(n_splits=5)
    splits = [
        ("held_out_staff", fold, train, test)
        for fold, (train, test) in enumerate(splitter.split(df, groups=df["staff_id"]))
    ]
    # Use actual observation intervals for the boundary, including overnight work.
    cutoff = pd.Timestamp("2024-07-13")
    dates = pd.to_datetime(df["date"])
    starts = dates + pd.to_timedelta(df["episode_start_min_from_date"], unit="min")
    ends = dates + pd.to_timedelta(df["episode_end_min_from_date"], unit="min")
    early = np.flatnonzero(ends <= cutoff)
    late = np.flatnonzero(starts >= cutoff)
    assert len(early) and len(late) and ends.iloc[early].max() <= starts.iloc[late].min()
    splits.append(("later_time", 0, early, late))
    results, folds = [], []
    for split, fold, train_idx, test_idx in splits:
        train, test = df.iloc[train_idx], df.iloc[test_idx]
        overlap = sorted(set(train["staff_id"]) & set(test["staff_id"]))
        assert split != "held_out_staff" or not overlap
        model_predictions = predict_options(train, test)
        result = test[["episode_id", "staff_id", "actual_duration_min"]].copy()
        result["split"], result["fold"] = split, fold
        for name, values in model_predictions.items():
            assert np.isfinite(values).all() and (values > 0).all()
            result[name] = values
        results.append(result)
        folds.append({
            "split": split, "fold": fold, "train_n": len(train), "test_n": len(test),
            "train_staff": sorted(train["staff_id"].unique()),
            "test_staff": sorted(test["staff_id"].unique()),
            "staff_overlap_n": len(overlap),
            "unseen_activity_n": int((~test["task_name"].isin(train["task_name"])).sum()),
            "models": {name: metrics(test["actual_duration_min"], value)
                       for name, value in model_predictions.items()},
        })
    predictions = pd.concat(results, ignore_index=True)
    scores = []
    for split, group in predictions.groupby("split", sort=False):
        assert group["episode_id"].is_unique
        for model in model_predictions:
            scores.append({"split": split, "model": model, "n": len(group),
                           **metrics(group["actual_duration_min"], group[model])})
    scores = pd.DataFrame(scores)
    assert len(predictions.query('split == "held_out_staff"')) == len(df)
    output_dir.mkdir(parents=True, exist_ok=True)
    scores.to_csv(output_dir / "duration_options_metrics.csv", index=False, lineterminator="\n")
    predictions.to_csv(output_dir / "duration_options_predictions.csv", index=False, lineterminator="\n")
    summary = {
        "status": "exploratory_fixed_options_no_hyperparameter_search",
        "target_kind": "observed_activity_episode", "seed": 42,
        "model_features": {
            "activity_median": ["task_name"],
            "activity_mean": ["task_name"],
            "hierarchical_median": ["task_name", "nurseflow_task_type"],
            "gradient_boosting": FEATURE_COLUMNS,
            "gb_absolute_name": ["task_name"],
            "gb_log_name": ["task_name"],
        },
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [features_path, episodes_path]},
        "later_time_cutoff": cutoff.isoformat(),
        "crossing_boundary_episodes_excluded": len(df) - len(early) - len(late),
        "folds": folds, "scores": scores.to_dict(orient="records"),
    }
    (output_dir / "duration_options_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return scores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proc-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    print(compare_options(args.proc_dir, args.output_dir).to_string(index=False))


if __name__ == "__main__":
    main()
