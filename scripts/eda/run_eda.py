"""Reproduce the selected-source EDA and grouped activity-duration experiment.

Extends Kien's preliminary EDA. Evaluation is on OR activity episodes, not
patient-level ward tasks, and does not deploy an L3 model.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from harmonize_and_engineer import (
    FEATURE_COLUMNS, GROUP_COLUMN, TARGET_COLUMN, validate_activity_features,
)


def hourly_minutes(segments):
    """Allocate actual segment overlap to each clock hour, including midnight."""
    hours = np.zeros(24)
    for start, end in segments[[
        "task_start_min_from_date", "task_end_min_from_date"
    ]].itertuples(index=False, name=None):
        cursor = float(start)
        while cursor < end:
            hour = int(cursor // 60)
            stop = min(float(end), (hour + 1) * 60)
            hours[hour % 24] += stop - cursor
            cursor = stop
    return hours.round(6).tolist()


def metrics(actual, prediction):
    return {
        "mae_min": round(float(mean_absolute_error(actual, prediction)), 4),
        "rmse_min": round(float(np.sqrt(mean_squared_error(actual, prediction))), 4),
        "r2": round(float(r2_score(actual, prediction)), 4) if len(actual) > 1 else None,
    }


def run_l3_predictability_gate(l3_df):
    """Compare train-only lookups and one GBT with staff-disjoint held-out rows."""
    df = l3_df[l3_df["nurseflow_task_type"] != "break"].reset_index(drop=True)
    n_groups = int(df[GROUP_COLUMN].nunique())
    if n_groups < 2:
        raise ValueError("Need at least two independent staff groups for evaluation")
    splitter = GroupKFold(n_splits=min(5, n_groups))
    predictions = df[["episode_id", GROUP_COLUMN, "nurseflow_task_type", TARGET_COLUMN]].copy()
    methods = ["global_median", "task_type_median", "activity_median", "activity_mean", "gradient_boosting"]
    for method in methods:
        predictions[method] = np.nan
    predictions["fold"] = -1
    folds = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(df, groups=df[GROUP_COLUMN])):
        train, test = df.iloc[train_idx], df.iloc[test_idx]
        train_groups = set(train[GROUP_COLUMN])
        test_groups = set(test[GROUP_COLUMN])
        if not train_groups.isdisjoint(test_groups):
            raise ValueError("Staff group leakage")
        global_median = float(train[TARGET_COLUMN].median())
        predictions.loc[test_idx, "global_median"] = global_median
        unseen = {}
        for method, key, statistic, fallback in [
            ("task_type_median", "nurseflow_task_type", "median", global_median),
            ("activity_median", "task_name", "median", global_median),
            ("activity_mean", "task_name", "mean", train[TARGET_COLUMN].mean()),
        ]:
            lookup = train.groupby(key)[TARGET_COLUMN].agg(statistic)
            mapped = test[key].map(lookup)
            unseen[method] = int(mapped.isna().sum())
            predictions.loc[test_idx, method] = mapped.fillna(fallback).to_numpy()
        encoder = ColumnTransformer([
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), FEATURE_COLUMNS)
        ])
        model = Pipeline([
            ("encode", encoder),
            ("model", GradientBoostingRegressor(
                n_estimators=180, max_depth=4, learning_rate=0.05, random_state=42
            )),
        ])
        model.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
        predictions.loc[test_idx, "gradient_boosting"] = np.maximum(
            model.predict(test[FEATURE_COLUMNS]), 0.01
        )
        predictions.loc[test_idx, "fold"] = fold
        folds.append({
            "fold": fold, "train_rows": len(train), "test_rows": len(test),
            "train_groups": sorted(train_groups), "test_groups": sorted(test_groups),
            "unseen_category_fallback_rows": unseen,
            "models": {name: metrics(test[TARGET_COLUMN], predictions.loc[test_idx, name]) for name in methods},
        })
    if predictions[methods].isna().any().any() or predictions["fold"].lt(0).any():
        raise ValueError("Incomplete out-of-fold predictions")
    result = {
        "n_episodes": len(df), "staff_groups": n_groups,
        "split_method": "GroupKFold(staff_id)", "n_splits": len(folds), "model_seed": 42,
        "target_kind": "observed_activity_episode", "feature_columns": FEATURE_COLUMNS,
        "metric_aggregation": "pooled_out_of_fold", "folds": folds,
        "models": {name: metrics(predictions[TARGET_COLUMN], predictions[name]) for name in methods},
    }
    result["best_mae_method"] = min(methods, key=lambda name: result["models"][name]["mae_min"])
    result["best_rmse_method"] = min(methods, key=lambda name: result["models"][name]["rmse_min"])
    return result, predictions


def md_table(frame):
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |",
             "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(v).replace("|", "/") for v in row) + " |")
    return "\n".join(lines)


def generate_figures(episodes, hours, evaluation, fig_dir):
    fig_dir.mkdir(parents=True, exist_ok=True)
    figures = []
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    types = episodes.groupby("nurseflow_task_type")["episode_duration_min"].median().sort_values()
    axes[0].barh(types.index, types.values)
    axes[0].set_xlabel("Median episode duration (minutes)")
    shares = episodes.groupby("nursing_class")["episode_duration_min"].sum()
    axes[1].bar(shares.index, shares / shares.sum() * 100)
    axes[1].set_ylabel("Share of observed minutes (%)")
    axes[1].set_title("Local source classification")
    fig.tight_layout()
    path = fig_dir / "eda_01_activity_duration.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    figures.append(path.name)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].bar(range(24), hours)
    axes[0].set_xlabel("Clock hour")
    axes[0].set_ylabel("Observed staff-minutes (all shifts)")
    axes[0].set_title("Segment overlap, including breaks")
    names = list(evaluation["models"])
    values = [evaluation["models"][name]["mae_min"] for name in names]
    axes[1].barh(names, values)
    axes[1].set_xlabel("Pooled OOF MAE (minutes)")
    axes[1].set_title("Held-out staff, OR activity episodes only")
    for i, value in enumerate(values):
        axes[1].text(value, i, f" {value:.2f}", va="center")
    axes[1].set_xlim(0, max(values) * 1.2)
    fig.tight_layout()
    path = fig_dir / "eda_02_hourly_and_validation.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    figures.append(path.name)
    return figures


def run_eda(proc_dir, fig_dir, report_path, summary_json):
    segments = pd.read_csv(proc_dir / "zenodo_tasks_en.csv")
    episodes = pd.read_csv(proc_dir / "zenodo_task_episodes_en.csv")
    features = pd.read_csv(proc_dir / "l3_activity_features.csv")
    validate_activity_features(features, episodes)
    glossary = json.loads((proc_dir / "zenodo_translation_glossary.json").read_text(encoding="utf-8"))
    stats = episodes.groupby("nurseflow_task_type")["episode_duration_min"].agg(
        episodes="count", median_min="median", mean_min="mean", std_min="std", max_min="max"
    )
    stats["p95_min"] = episodes.groupby("nurseflow_task_type")["episode_duration_min"].quantile(0.95)
    outliers = {}
    for key, group in episodes.groupby("nurseflow_task_type"):
        duration = group["episode_duration_min"]
        q1, q3 = duration.quantile([0.25, 0.75])
        outliers[key] = int(((duration < q1 - 1.5 * (q3 - q1)) | (duration > q3 + 1.5 * (q3 - q1))).sum())
    stats["iqr_outliers"] = pd.Series(outliers)
    stats = stats.round(3).sort_values("episodes", ascending=False).reset_index()
    stats.to_csv(proc_dir / "duration_by_type.csv", index=False, lineterminator="\n")
    hours = hourly_minutes(segments)
    if not np.isclose(sum(hours), segments["actual_duration_min"].sum()):
        raise ValueError("Hourly allocation does not conserve recorded time")
    starts = episodes.loc[episodes["nurseflow_task_type"] != "break", "hour_of_day"].value_counts()
    starts = starts.reindex(range(24), fill_value=0)
    evaluation, predictions = run_l3_predictability_gate(features)
    predictions.to_csv(proc_dir / "l3_oof_predictions.csv", index=False, lineterminator="\n")
    absolute_error = (predictions[TARGET_COLUMN] - predictions["activity_median"]).abs()
    procedure = predictions["nurseflow_task_type"].eq("procedure_care")
    by_type = []
    for task_type, group in predictions.groupby("nurseflow_task_type"):
        for method in evaluation["models"]:
            by_type.append({"task_type": task_type, "model": method, "n": len(group),
                            **metrics(group[TARGET_COLUMN], group[method])})
    pd.DataFrame(by_type).to_csv(proc_dir / "l3_metrics_by_type.csv", index=False, lineterminator="\n")
    missing = {name: {key: int(count) for key, count in frame.isna().sum().items() if count}
               for name, frame in [("segments", segments), ("episodes", episodes), ("features", features)]}
    missing_rows = []
    for stage, counts, denominator in [
        ("raw", glossary["raw_missing_counts"], glossary["raw_records"]),
        ("clean_segments", segments.isna().sum().to_dict(), len(segments)),
        ("clean_episodes", episodes.isna().sum().to_dict(), len(episodes)),
        ("features", features.isna().sum().to_dict(), len(features)),
    ]:
        for column, count in counts.items():
            missing_rows.append({"stage": stage, "column": column, "missing_n": int(count),
                                 "n": denominator, "missing_pct": round(100 * count / denominator, 4)})
    pd.DataFrame(missing_rows).to_csv(proc_dir / "missingness.csv", index=False, lineterminator="\n")
    shift_keys = ["staff_id", "date", "shift_code", "shift_start_hhmmss", "shift_end_hhmmss"]
    figures = generate_figures(episodes, hours, evaluation, fig_dir)
    summary = {
        "source": "10.5281/zenodo.20754938", "source_md5": glossary["source_md5"],
        "counts": {
            "raw_segments": glossary["raw_records"], "clean_segments": len(segments),
            "duplicates_removed": len(glossary["dropped_duplicate_excel_rows"]),
            "raw_minutes": glossary["raw_minutes"], "clean_minutes": float(segments["actual_duration_min"].sum()),
            "episodes": len(episodes), "non_break_episodes": len(features),
            "staff": int(segments["staff_id"].nunique()),
            "staff_shifts": len(segments[shift_keys].drop_duplicates()),
            "activity_labels": int(episodes["task_name"].nunique()),
            "activity_categories": int(episodes["task_category"].nunique()),
            "midnight_wraps": glossary["midnight_wraps"],
        },
        "missing_counts": missing,
        "raw_missing_counts": glossary["raw_missing_counts"],
        "categorical_cardinality": {key: int(episodes[key].nunique()) for key in [
            "task_name", "task_category", "nurseflow_task_type", "shift_code", "staff_id"
        ]},
        "class_minutes": {key: float(value) for key, value in episodes.groupby("nursing_class")["episode_duration_min"].sum().items()},
        "hourly_minutes": hours,
        "hourly_non_break_episode_starts": starts.tolist(),
        "patient_acuity_duration_correlation": {"status": "not_estimable", "reason": "No linked patient/acuity/ADL observations in the workbook"},
        "activity_median_error": {
            "median_absolute_error_min": float(absolute_error.median()),
            "procedure_care_n": int(procedure.sum()),
            "procedure_care_absolute_error_min": float(absolute_error[procedure].sum()),
            "total_absolute_error_min": float(absolute_error.sum()),
        },
        "evaluation": evaluation, "figures": figures,
        "versions": {"python": sys.version.split()[0], "pandas": pd.__version__,
                     "numpy": np.__version__, "sklearn": sklearn.__version__, "matplotlib": matplotlib.__version__},
        "feature_sha256": hashlib.sha256((proc_dir / "l3_activity_features.csv").read_bytes()).hexdigest(),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # The report has a reviewed decision/mapping section, followed by reproducible numbers.
    decision = (Path(__file__).resolve().parents[2] / "docs/eda-report.md").read_text(encoding="utf-8").partition("<!-- EDA_RESULTS -->")[0].rstrip()
    model_table = pd.DataFrame([{"method": name, **value} for name, value in evaluation["models"].items()])
    stats_table = stats[[
        "nurseflow_task_type", "episodes", "median_min", "p95_min", "iqr_outliers"
    ]].rename(columns={
        "nurseflow_task_type": "Nhóm hoạt động", "episodes": "Số episode",
        "median_min": "Trung vị (phút)", "p95_min": "P95 (phút)",
        "iqr_outliers": "Outlier",
    })
    model_table = model_table.rename(columns={
        "method": "Phương pháp", "mae_min": "MAE (phút)",
        "rmse_min": "RMSE (phút)", "r2": "R²",
    })
    counts = summary["counts"]
    body = f"""{decision}

<!-- EDA_RESULTS -->

## 4. Kết quả EDA

Dữ liệu raw có {counts['raw_segments']:,} segment, tổng {counts['raw_minutes']:,.0f} phút.
Sau bỏ {counts['duplicates_removed']} dòng trùng còn {counts['clean_segments']:,} segment,
{counts['clean_minutes']:,.0f} phút, {counts['episodes']:,} activity episode của
{counts['staff']} nhân viên trong {counts['staff_shifts']} staff-shift. Có
{counts['activity_labels']} nhãn, {counts['activity_categories']} category và {counts['midnight_wraps']} lượt qua 0h.

### 4.1. Phân phối và dữ liệu thiếu

{md_table(stats_table)}

Outlier là giá trị nhỏ hơn Q1 − 1,5 × IQR hoặc lớn hơn Q3 + 1,5 × IQR của từng nhóm task.
[Thống kê đầy đủ mean, SD, max và p95](../data/processed/duration_by_type.csv).
Nhóm hiếm nhất là safety_prep với 6 episode, medication_preparation có 15 episode.
Cần xét quy mô từng nhóm khi đọc các giá trị median và p95.

Ở mức segment, {missing['segments']['shift_end_hhmmss']} dòng thiếu giờ kết thúc ca.
Ở mức episode có {missing['episodes']['shift_end_hhmmss']} dòng thiếu.
Có {glossary['raw_missing_counts']['overtime_status']:,} dòng raw trống overtime được giữ
là Unspecified. Bảng feature chọn được các cột có dữ liệu liên kết đầy đủ.
Acuity/ADL ↔ duration chưa tính được do thiếu liên kết bệnh nhân.
[Số thiếu và tỷ lệ từng bước](../data/processed/missingness.csv).

![Thời lượng và cơ cấu hoạt động](figures/{figures[0]})

Nhãn Nursing/Non-Nursing/Break theo phân loại địa phương của nguồn. Tổng staff-minutes theo giờ
được tính từ phần giao của segment với từng giờ và bằng {sum(hours):,.0f} phút.
Trong {int(starts.sum()):,} lượt bắt đầu hoạt động làm việc, khung
{int(starts.idxmax()):02d}h–{int(starts.idxmax()+1):02d}h có nhiều nhất, {int(starts.max())} lượt trong tuần.
Muốn suy nhu cầu theo giờ còn cần mẫu số nhân lực và bệnh nhân.

### 4.2. Đánh giá thời lượng

Đánh giá trên {counts['non_break_episodes']:,} episode làm việc với {evaluation['n_splits']} folds
GroupKFold theo staff. Encoder, bảng tra và model được fit trên train của từng fold.
MAE/RMSE/R² được tính gộp từ dự đoán out-of-fold. Khi gặp nhãn mới, bảng tra dùng thống kê
tương ứng trên toàn train. Boosting dùng ba cột categorical, seed 42 và cấu hình cố định.

{md_table(model_table)}

Median theo tên đạt MAE {evaluation['models']['activity_median']['mae_min']:.2f} phút,
trung vị sai số tuyệt đối {absolute_error.median():.0f} phút. Nhóm procedure_care có
{int(procedure.sum())}/{len(predictions)} episode và đóng góp
{100 * absolute_error[procedure].sum() / absolute_error.sum():.1f}% tổng sai số tuyệt đối.
Boosting đạt RMSE {evaluation['models']['gradient_boosting']['rmse_min']:.2f} phút,
so với {evaluation['models']['activity_mean']['rmse_min']:.2f} phút của mean theo tên.
[Sai số từng nhóm task](../data/processed/l3_metrics_by_type.csv) · [Dự đoán OOF](../data/processed/l3_oof_predictions.csv).

![Phân bố theo giờ và sai số dự đoán](figures/{figures[1]})

Nhóm thử thêm median fallback theo nhóm task, boosting tối ưu MAE và boosting trên log-duration.
Các phương án được kiểm bằng cùng các fold theo staff và một phép chia riêng tại 00h ngày
13/7/2024. Episode băng qua mốc được loại khỏi phép kiểm theo thời gian. Bảng kết quả cho thấy
median phân cấp chỉ cải thiện rất nhỏ, còn thứ hạng model thay đổi trên mẫu cuối tuần.
[Kết quả các phương án](../data/processed/duration_options_metrics.csv) · [Fold và checksum](../data/processed/duration_options_summary.json).

## 5. Kết luận và phạm vi áp dụng

Nhóm chọn median theo task_name làm baseline duration cho thí nghiệm OR vì cách tra đơn giản
và MAE cạnh tranh trên các cấu hình đã kiểm. Hai cột nhóm được giữ để tổng hợp và đối chứng.
Kết quả phụ thuộc cách chia và cơ cấu mẫu, đặc biệt mẫu cuối tuần nhỏ. Workbook thiếu mã ca mổ
và bệnh nhân để kiểm độc lập theo hai đơn vị đó. Chia theo staff vẫn có thể chứa các hoạt động
cùng bối cảnh ở hai phía train/test. Phạm vi đánh giá hiện tại là một bệnh viện trong một tuần.

Với bài toán nội trú của NurseFlow, nhóm chọn given/lookup có nguồn cho L3. Việc học ảnh hưởng
của acuity, ADL và kinh nghiệm cần thêm dữ liệu task–patient liên kết. Roster, required_skill,
coverage, deadline và chính sách nghỉ do input/kịch bản cung cấp theo contract.
Kết quả Preliminary hỗ trợ chuẩn bị dữ liệu cho các bước L1–L4. Đánh giá sản phẩm CP3 sử dụng
benchmark hội thoại, lượt gọi AI thật và run ID theo rubric BTC. B19–B20 bổ sung từ hai nguồn
được chọn để kiểm nhầm lẫn preparation/admin và điều kiện dùng lookup mobility. Bộ hiện tại
có 20 câu, trong đó 8 câu từ dữ liệu công khai.
[Hồ sơ benchmark](../eval/README.md).
[Quy định CP3](https://github.com/VinUni-AI20k/K5-L3-Day15-AI-Product-Hackathon/blob/b568b951dfc0342e84c357bd09405d8e7040ebb6/README.md#checkpoint).

## 6. Tái lập và đóng góp

Cài dependency trong requirements.txt, chạy từ thư mục gốc theo thứ tự sau.

```bash
python scripts/data/translate_zenodo.py
python scripts/data/harmonize_and_engineer.py
python scripts/eda/run_eda.py
python scripts/eda/compare_duration_options.py
python scripts/data/build_preliminary_handoff.py
python scripts/data/check_preliminary_handoff.py
python -B -m unittest discover -s tests -v
python -B run.py check
```

Phiên bản thư viện và checksum được ghi trong [eda_summary.json](../data/processed/eda_summary.json).

Lam và Kiên phụ trách nghiên cứu, lựa chọn dữ liệu và phương pháp. Kiên đề xuất nguồn,
thực hiện pipeline, bản dịch và EDA ban đầu. Lam chủ trì kiểm chứng, hoàn thiện xử lý,
feature và phương án bàn giao. Codex được sử dụng để tham vấn, hỗ trợ lập trình,
kiểm tra kết quả và biên tập báo cáo.
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(body, encoding="utf-8")
    return {"counts": counts, "models": evaluation["models"], "report": str(report_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proc-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--fig-dir", type=Path, default=Path("docs/figures"))
    parser.add_argument("--report", type=Path, default=Path("docs/eda-report.md"))
    parser.add_argument("--summary", type=Path, default=Path("data/processed/eda_summary.json"))
    args = parser.parse_args()
    print(json.dumps(run_eda(args.proc_dir, args.fig_dir, args.report, args.summary), ensure_ascii=False))


if __name__ == "__main__":
    main()
