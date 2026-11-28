"""L3 thực nghiệm: dự đoán thời lượng activity episode PHÒNG MỔ (Zenodo 20754938).

Nhánh nghiên cứu, tách khỏi estimator production nội trú (codebase/workload). Kết quả KHÔNG
được dùng làm duration chăm sóc bệnh nhân nội trú và model KHÔNG được nạp vào production.

Protocol (giống Preliminary của Lam, scripts/eda/compare_duration_options.py):
- Dữ liệu: data/processed/l3_activity_features.csv (chỉ đọc), feature = task_name,
  nurseflow_task_type, task_category. Target = actual_duration_min (phút episode OR quan sát).
- Chia: GroupKFold(5) theo staff_id (không xáo, tất định) + holdout thời gian cutoff 2024-07-13.
- Mọi encoder/thống kê/hyperparameter chỉ fit trên train của từng fold. Chỉ Ridge chọn alpha,
  bằng GroupKFold lồng trên train. Seed 42.

Chạy: python scripts/l3/train_or_experiment.py   (ghi vào artifacts/l3/)
"""
import argparse
import hashlib
import json
import platform
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "data"))
from harmonize_and_engineer import (FEATURE_COLUMNS, GROUP_COLUMN, TARGET_COLUMN,  # noqa: E402
                                    validate_activity_features)

SEED = 42
CUTOFF = pd.Timestamp("2024-07-13")
DATASET_URL = "https://zenodo.org/records/20754938"
MODELS = ["global_median", "task_type_median", "activity_median", "ridge",
          "random_forest", "gradient_boosting", "mlp"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def encoder():
    return OneHotEncoder(handle_unknown="ignore", sparse_output=False)


def build_model(name, groups):
    """Mô hình học; tham số cố định, không tìm kiếm trên test."""
    if name == "ridge":
        inner = max(2, min(5, len(set(groups))))
        cv = list(GroupKFold(n_splits=inner).split(np.zeros(len(groups)), groups=groups))
        return make_pipeline(encoder(), RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0], cv=cv))
    if name == "random_forest":
        return make_pipeline(encoder(), RandomForestRegressor(
            n_estimators=300, min_samples_leaf=5, random_state=SEED, n_jobs=-1))
    if name == "gradient_boosting":
        # Cùng cấu hình GBT của Preliminary để so sánh trực tiếp.
        return make_pipeline(encoder(), GradientBoostingRegressor(
            n_estimators=180, max_depth=4, learning_rate=0.05, random_state=SEED))
    if name == "mlp":
        # Mạng nhỏ 2 tầng ẩn; target chuẩn hóa để hội tụ; early stopping lấy 15% CỦA TRAIN.
        net = MLPRegressor(hidden_layer_sizes=(32, 16), alpha=1e-3, learning_rate_init=1e-3,
                           max_iter=2000, early_stopping=True, validation_fraction=0.15,
                           n_iter_no_change=30, random_state=SEED)
        return make_pipeline(encoder(), TransformedTargetRegressor(regressor=net, transformer=StandardScaler()))
    raise ValueError(name)


def predict_fold(train, test):
    y = train[TARGET_COLUMN]
    global_median = y.median()
    type_median = train.groupby("nurseflow_task_type")[TARGET_COLUMN].median()
    name_median = train.groupby("task_name")[TARGET_COLUMN].median()
    type_pred = test["nurseflow_task_type"].map(type_median).fillna(global_median)
    out = {
        "global_median": np.full(len(test), global_median, dtype=float),
        "task_type_median": type_pred.to_numpy(float),
        # Phân cấp: tên hoạt động → nhóm task → toàn cục (giống hierarchical_median của Lam).
        "activity_median": test["task_name"].map(name_median).fillna(type_pred).to_numpy(float),
    }
    notes = {}
    for name in MODELS[3:]:
        model = build_model(name, train[GROUP_COLUMN].to_numpy())
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(train[FEATURE_COLUMNS], y)
        notes[name] = {"convergence_warnings": sum(issubclass(w.category, ConvergenceWarning) for w in caught)}
        if name == "ridge":
            notes[name]["alpha"] = float(model[-1].alpha_)
        if name == "mlp":
            notes[name]["n_iter"] = int(model[-1].regressor_.n_iter_)
        # Duration phải dương: chặn dưới 1 phút (giá trị nhỏ nhất quan sát được trong dữ liệu).
        out[name] = np.maximum(model.predict(test[FEATURE_COLUMNS]), 1.0)
    return out, notes


def metrics(actual, predicted):
    """Công thức (n = số episode đánh giá):
    MAE = mean|ŷ−y| · RMSE = sqrt(mean(ŷ−y)²) · R² = 1 − SSres/SStot · MedAE = median|ŷ−y|
    underestimate_rate = #(ŷ<y)/n · mean_underestimate = mean(y−ŷ | ŷ<y) (mẫu số: số ca thiếu)
    max_underestimate = max(y−ŷ) · P90/P95 = phân vị 90/95 của |ŷ−y|.
    """
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    err = predicted - actual
    abs_err = np.abs(err)
    under = -err[err < 0]
    ss_tot = ((actual - actual.mean()) ** 2).sum()
    return {
        "n": int(len(actual)),
        "mae": float(abs_err.mean()), "rmse": float(np.sqrt((err ** 2).mean())),
        "r2": float(1 - (err ** 2).sum() / ss_tot) if ss_tot else None,
        "median_ae": float(np.median(abs_err)),
        "p90_ae": float(np.percentile(abs_err, 90)), "p95_ae": float(np.percentile(abs_err, 95)),
        "underestimate_rate": float(len(under) / len(err)),
        "mean_underestimate": float(under.mean()) if len(under) else 0.0,
        "max_underestimate": float(under.max()) if len(under) else 0.0,
        "bias": float(err.mean()),
    }


def load(proc_dir):
    features_path = proc_dir / "l3_activity_features.csv"
    episodes_path = proc_dir / "zenodo_task_episodes_en.csv"
    features, episodes = pd.read_csv(features_path), pd.read_csv(episodes_path)
    validate_activity_features(features, episodes)
    df = features.merge(episodes[["episode_id", "episode_start_min_from_date", "episode_end_min_from_date"]],
                        on="episode_id", validate="one_to_one")
    # Mốc thời gian chỉ dùng để CHIA holdout, không làm feature.
    dates = pd.to_datetime(df["date"])
    df["_start"] = dates + pd.to_timedelta(df["episode_start_min_from_date"], unit="min")
    df["_end"] = dates + pd.to_timedelta(df["episode_end_min_from_date"], unit="min")
    checks = {
        "rows": len(df), "staff": int(df[GROUP_COLUMN].nunique()),
        "date_min": str(df["date"].min()), "date_max": str(df["date"].max()),
        "missing_cells": int(features.isna().sum().sum()),
        "duplicate_episode_id": int(features["episode_id"].duplicated().sum()),
        "duplicate_rows_excluding_id": int(features.drop(columns="episode_id").duplicated().sum()),
        "non_positive_target": int((df[TARGET_COLUMN] <= 0).sum()),
        "task_name_levels": int(df["task_name"].nunique()),
        "task_type_levels": int(df["nurseflow_task_type"].nunique()),
        "task_category_levels": int(df["task_category"].nunique()),
        "task_name_determines_type": bool((df.groupby("task_name")["nurseflow_task_type"].nunique() == 1).all()),
        "task_name_determines_category": bool((df.groupby("task_name")["task_category"].nunique() == 1).all()),
        "target_quantiles": {str(q): float(df[TARGET_COLUMN].quantile(q)) for q in (0.5, 0.75, 0.9, 0.95, 0.99)},
        "target_mean": float(df[TARGET_COLUMN].mean()), "target_max": float(df[TARGET_COLUMN].max()),
        "iqr_outliers_kept": int((df[TARGET_COLUMN] > df[TARGET_COLUMN].quantile(.75)
                                  + 1.5 * (df[TARGET_COLUMN].quantile(.75) - df[TARGET_COLUMN].quantile(.25))).sum()),
    }
    sources = {p.name: sha256(p) for p in (features_path, episodes_path)}
    return df, checks, sources


def run(proc_dir, out_dir):
    df, checks, sources = load(proc_dir)
    splits = [("held_out_staff", f, tr, te) for f, (tr, te)
              in enumerate(GroupKFold(n_splits=5).split(df, groups=df[GROUP_COLUMN]))]
    early = np.flatnonzero(df["_end"] <= CUTOFF)
    late = np.flatnonzero(df["_start"] >= CUTOFF)
    splits.append(("later_time", 0, early, late))

    rows, folds = [], []
    for split, fold, tr, te in splits:
        train, test = df.iloc[tr], df.iloc[te]
        if split == "held_out_staff":
            assert not set(train[GROUP_COLUMN]) & set(test[GROUP_COLUMN]), "staff rò rỉ giữa train/test"
        preds, notes = predict_fold(train, test)
        frame = test[["episode_id", GROUP_COLUMN, "task_name", "nurseflow_task_type", TARGET_COLUMN]].copy()
        frame["split"], frame["fold"] = split, fold
        for name in MODELS:
            assert np.isfinite(preds[name]).all() and (preds[name] > 0).all()
            frame[name] = preds[name]
        rows.append(frame)
        folds.append({"split": split, "fold": fold, "train_n": len(train), "test_n": len(test),
                      "test_staff": sorted(test[GROUP_COLUMN].unique()),
                      "unseen_task_name_n": int((~test["task_name"].isin(train["task_name"])).sum()),
                      "notes": notes,
                      "metrics": {m: metrics(test[TARGET_COLUMN], preds[m]) for m in MODELS}})
    pred = pd.concat(rows, ignore_index=True)
    staff = pred[pred["split"] == "held_out_staff"]
    assert len(staff) == len(df) and staff["episode_id"].is_unique

    overall = {split: {m: metrics(g[TARGET_COLUMN], g[m]) for m in MODELS}
               for split, g in pred.groupby("split", sort=False)}
    fold_mae = {m: [f["metrics"][m]["mae"] for f in folds if f["split"] == "held_out_staff"] for m in MODELS}
    stability = {m: {"fold_mae_mean": float(np.mean(v)), "fold_mae_std": float(np.std(v, ddof=1))}
                 for m, v in fold_mae.items()}
    by_type = [{"task_type": t, "model": m, **metrics(g[TARGET_COLUMN], g[m])}
               for t, g in staff.groupby("nurseflow_task_type") for m in MODELS]
    by_name = [{"task_name": t, "n": len(g), "model": m, **metrics(g[TARGET_COLUMN], g[m])}
               for t, g in staff.groupby("task_name") if len(g) >= 20 for m in MODELS]

    out_dir.mkdir(parents=True, exist_ok=True)
    pred.drop(columns=[]).to_csv(out_dir / "or_oof_predictions.csv", index=False, lineterminator="\n")
    pd.DataFrame(by_type).to_csv(out_dir / "or_metrics_by_task_type.csv", index=False, lineterminator="\n")
    pd.DataFrame(by_name).to_csv(out_dir / "or_metrics_by_task_name.csv", index=False, lineterminator="\n")
    summary = {
        "status": "experimental_or_only_not_for_inpatient_production",
        "dataset": {"source": DATASET_URL, "file_sha256": sources, "checks": checks},
        "target": {"name": TARGET_COLUMN, "unit": "phút activity episode phòng mổ quan sát được",
                   "not": "thời lượng chăm sóc một bệnh nhân nội trú"},
        "features": FEATURE_COLUMNS,
        "excluded_columns": ["episode_id", "staff_id (chỉ chia fold)", "date/start/end (chỉ chia holdout)",
                             "source_excel_rows", "actual_duration_min (target)", "target_kind", "source_dataset"],
        "protocol": {"cv": "GroupKFold(n_splits=5) theo staff_id, không xáo",
                     "temporal_holdout": "train: kết thúc ≤ %s; test: bắt đầu ≥ %s; episode cắt mốc bị loại"
                                         % (CUTOFF.date(), CUTOFF.date()),
                     "temporal_excluded": int(len(df) - len(early) - len(late)),
                     "hyperparameters": "cố định; Ridge chọn alpha bằng GroupKFold lồng trên train",
                     "prediction_floor_min": 1.0, "seed": SEED, "aggregation": "pooled out-of-fold"},
        "overall": overall, "stability": stability, "folds": folds,
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "pandas": pd.__version__, "numpy": np.__version__},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out_dir / "or_experiment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--proc-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "l3")
    args = parser.parse_args()
    summary = run(args.proc_dir, args.out_dir)
    for split, table in summary["overall"].items():
        print("\n== %s (n=%d)" % (split, next(iter(table.values()))["n"]))
        print(pd.DataFrame(table).T[["mae", "rmse", "r2", "median_ae", "p95_ae",
                                     "underestimate_rate", "mean_underestimate"]].round(3).to_string())


if __name__ == "__main__":
    main()
