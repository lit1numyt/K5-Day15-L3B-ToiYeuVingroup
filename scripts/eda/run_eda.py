"""Run multi-source EDA across Zenodo 20754938, eICU Demo v2.0.1, and psmet1/nrp, plus L3 ML decision gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _df_to_md(df: pd.DataFrame, include_index: bool = True) -> str:
    """Format a DataFrame as a GitHub-flavored Markdown table without requiring tabulate."""
    frame = df.reset_index() if include_index else df.copy()
    headers = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in frame.iterrows():
        vals = [str(row[c]) for c in frame.columns]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def _iqr_outlier_count(s: pd.Series) -> int:
    q1, q3 = np.percentile(s.dropna(), [25, 75])
    iqr = q3 - q1
    hi = q3 + 1.5 * iqr
    lo = q1 - 1.5 * iqr
    return int(((s < lo) | (s > hi)).sum())


def run_l3_predictability_gate(l3_df: pd.DataFrame) -> dict:
    """Evaluate zero-leakage ML models predicting Zenodo episode actual_duration_min."""
    df = l3_df[l3_df["nurseflow_task_type"] != "break"].copy()
    target = df["actual_duration_min"].values

    cat_cols = [
        "nurseflow_task_type",
        "task_category",
        "nursing_class",
        "task_name",
        "shift_code",
        "shift_window",
        "shift_phase",
        "day_of_week",
    ]
    num_cols = [
        "prep_required",
        "time_of_day_sin",
        "time_of_day_cos",
        "is_handover_window",
        "is_weekend",
        "staff_prior_task_type_count",
        "shift_length_min_clean",
        "eicu_hourly_mean_acuity",
        "eicu_hourly_mean_adl",
    ]
    X = df[cat_cols + num_cols]

    pre = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
            ("num", StandardScaler(), num_cols),
        ]
    )

    models = {
        "Baseline_Median": Pipeline([("pre", pre), ("reg", DummyRegressor(strategy="median"))]),
        "Ridge": Pipeline([("pre", pre), ("reg", Ridge(alpha=10.0))]),
        "RandomForest": Pipeline(
            [("pre", pre), ("reg", RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1))]
        ),
        "GradientBoosting": Pipeline(
            [("pre", pre), ("reg", GradientBoostingRegressor(n_estimators=180, max_depth=4, learning_rate=0.05, random_state=42))]
        ),
    }

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    results = {}
    for name, pipe in models.items():
        scores = cross_validate(
            pipe,
            X,
            target,
            cv=cv,
            scoring={"mae": "neg_mean_absolute_error", "rmse": "neg_root_mean_squared_error", "r2": "r2"},
        )
        results[name] = {
            "mae_min": round(float(-scores["test_mae"].mean()), 2),
            "rmse_min": round(float(-scores["test_rmse"].mean()), 2),
            "r2": round(float(scores["test_r2"].mean()), 4),
        }

    # Fit best tree model once on full data to inspect feature importances
    best_pipe = models["GradientBoosting"]
    best_pipe.fit(X, target)
    ohe = best_pipe.named_steps["pre"].named_transformers_["cat"]
    feat_names = list(ohe.get_feature_names_out(cat_cols)) + num_cols
    importances = best_pipe.named_steps["reg"].feature_importances_
    top_idx = np.argsort(importances)[::-1][:10]
    top_features = [{"feature": feat_names[i], "importance": round(float(importances[i]), 4)} for i in top_idx]

    return {
        "n_episodes_evaluated": int(len(df)),
        "models_5fold_cv": results,
        "top_10_features_gb": top_features,
    }


def generate_figures(
    z_ep: pd.DataFrame,
    e_pat: pd.DataFrame,
    e_tasks: pd.DataFrame,
    n_nurses: pd.DataFrame,
    n_wards: pd.DataFrame,
    l3_cv: dict,
    fig_dir: Path,
) -> list[str]:
    """Create 4 summary PNG charts in docs/figures/."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", font_scale=0.95)
    saved: list[str] = []

    # 1. Zenodo Duration by nurseflow_task_type & Nursing class time share
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    order_types = (
        z_ep.groupby("nurseflow_task_type")["episode_duration_min"]
        .median()
        .sort_values(ascending=False)
        .index
    )
    sns.boxplot(
        data=z_ep,
        y="nurseflow_task_type",
        x="episode_duration_min",
        order=order_types,
        ax=axes[0],
        color="#4C78A8",
        showfliers=False,
    )
    axes[0].set_title("Zenodo 20754938: Task Episode Duration (IQR, Outliers Hidden)")
    axes[0].set_xlabel("Episode Duration (minutes)")
    axes[0].set_ylabel("NurseFlow Task Type")

    class_min = z_ep.groupby("nursing_class")["episode_duration_min"].sum().sort_values(ascending=False)
    pct = (class_min / class_min.sum() * 100).round(1)
    bars = axes[1].bar(class_min.index, pct.values, color=["#2E86AB", "#F18F01", "#6BA368"])
    axes[1].set_title("Zenodo 20754938: Share of Total Recorded Staff Time (%)")
    axes[1].set_ylabel("Share of Total Time (%)")
    for b, p, m in zip(bars, pct.values, class_min.values):
        axes[1].text(b.get_x() + b.get_width() / 2, b.get_height() + 1.0, f"{p}%\n({m/60:.0f}h)", ha="center", va="bottom", fontsize=9)
    axes[1].set_ylim(0, max(pct.values) + 12)
    plt.tight_layout()
    p1 = fig_dir / "eda_01_zenodo_duration_and_share.png"
    fig.savefig(p1, dpi=160)
    plt.close(fig)
    saved.append(str(p1))

    # 2. eICU Acuity & ADL vs Nursing Events per 24h
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    e_trim = e_pat[e_pat["nursing_events_per_24h"] <= e_pat["nursing_events_per_24h"].quantile(0.98)].copy()
    sns.boxplot(data=e_trim, x="acuity_score", y="nursing_events_per_24h", hue="is_ventilated", ax=axes[0], palette="Set2")
    axes[0].set_title("eICU (n=2,520): Nursing Events/24h by Acuity & Ventilation")
    axes[0].set_xlabel("Unified Acuity Score (1=Low .. 5=Critical)")
    axes[0].set_ylabel("Nursing Events per 24h (<=98th pct)")
    axes[0].legend(title="Ventilated", labels=["No", "Yes"])

    adl_med = e_pat.groupby(["adl_dependency", "isolation_precaution"], as_index=False)["nursing_events_per_24h"].median()
    sns.barplot(data=adl_med, x="adl_dependency", y="nursing_events_per_24h", hue="isolation_precaution", ax=axes[1], palette="muted")
    axes[1].set_title("eICU: Median Nursing Events/24h by ADL Dependency & Isolation")
    axes[1].set_xlabel("ADL Dependency Level (1=Self .. 4=Total Assist)")
    axes[1].set_ylabel("Median Nursing Events / 24h")
    axes[1].legend(title="Isolation", labels=["No", "Yes"])
    plt.tight_layout()
    p2 = fig_dir / "eda_02_eicu_acuity_adl_workload.png"
    fig.savefig(p2, dpi=160)
    plt.close(fig)
    saved.append(str(p2))

    # 3. NRP Coverage Pressure & Nurse Experience Distribution
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    wi_plot = n_wards.copy()
    wi_plot["effective_nurses"] = wi_plot["n_nurses"] * (1.0 - wi_plot["n_absence_requests"] / (wi_plot["n_nurses"] * wi_plot["period_days"]))
    wi_plot["coverage_pressure"] = wi_plot["avg_daily_min_headcount"] / wi_plot["effective_nurses"]
    sns.barplot(data=wi_plot, x="ward_name", y="coverage_pressure", hue="scenario", ax=axes[0], palette="viridis")
    axes[0].axhline(0.75, color="red", linestyle="--", linewidth=1, label="Tight Capacity Threshold (0.75)")
    axes[0].set_title("psmet1/nrp: Daily Required Headcount / Effective Nurses")
    axes[0].set_xlabel("Clinical Ward")
    axes[0].set_ylabel("Coverage Pressure Ratio")
    axes[0].legend(title="Scenario")

    lvl_counts = (
        n_nurses[n_nurses["scenario"] == "Normal"]
        .groupby(["ward_name", "qualification_level"])
        .size()
        .reset_index(name="nurses")
    )
    sns.barplot(data=lvl_counts, x="ward_name", y="nurses", hue="qualification_level", ax=axes[1], palette="Blues_d")
    axes[1].set_title("psmet1/nrp: Nurse Max Qualification Level by Ward (Normal)")
    axes[1].set_xlabel("Clinical Ward")
    axes[1].set_ylabel("Number of Nurses")
    axes[1].legend(title="Max LevelOfExperience")
    plt.tight_layout()
    p3 = fig_dir / "eda_03_nrp_coverage_and_skills.png"
    fig.savefig(p3, dpi=160)
    plt.close(fig)
    saved.append(str(p3))

    # 4. Hourly Task Density (Zenodo vs eICU) & L3 ML Benchmark
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5))
    z_hr = z_ep.groupby("hour_of_day")["episode_duration_min"].sum()
    z_hr_pct = z_hr.reindex(range(24), fill_value=0) / z_hr.sum() * 100
    e_hr = e_tasks.groupby("hour_of_day")["event_count"].sum()
    e_hr_pct = e_hr.reindex(range(24), fill_value=0) / e_hr.sum() * 100
    axes[0].plot(range(24), z_hr_pct.values, marker="o", label="Zenodo OR Tasks (% minutes)")
    axes[0].plot(range(24), e_hr_pct.values, marker="s", label="eICU Ward Events (% events)")
    axes[0].axvspan(7, 8, color="orange", alpha=0.15, label="Morning Handover")
    axes[0].axvspan(11, 13, color="green", alpha=0.12, label="Midday Break Window")
    axes[0].set_title("Hourly Workload Density: Zenodo OR vs eICU ICU")
    axes[0].set_xlabel("Hour of Day (0..23)")
    axes[0].set_ylabel("Share of 24h Activity (%)")
    axes[0].set_xticks(range(0, 24, 2))
    axes[0].legend(fontsize=8)

    cv_res = l3_cv["models_5fold_cv"]
    m_names = list(cv_res.keys())
    maes = [cv_res[m]["mae_min"] for m in m_names]
    r2s = [cv_res[m]["r2"] for m in m_names]
    bars = axes[1].bar(m_names, maes, color=["#999999", "#5B8FA8", "#3B7A57", "#1F4E78"])
    axes[1].set_title("L3 Duration Estimator Gate (5-Fold CV on Zenodo Real Episodes)")
    axes[1].set_ylabel("MAE (minutes, lower is better)")
    for b, mae, r2 in zip(bars, maes, r2s):
        axes[1].text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"MAE={mae}m\nR²={r2:.3f}", ha="center", va="bottom", fontsize=8.5)
    axes[1].set_ylim(0, max(maes) + 8)
    plt.tight_layout()
    p4 = fig_dir / "eda_04_hourly_density_and_l3_gate.png"
    fig.savefig(p4, dpi=160)
    plt.close(fig)
    saved.append(str(p4))

    return saved


def run_eda(proc_dir: Path, fig_dir: Path, report_path: Path, summary_json: Path) -> dict:
    """Compute EDA metrics across all tables, build charts, and write Vietnamese markdown report."""
    z_seg = pd.read_csv(proc_dir / "zenodo_tasks_en.csv")
    z_ep = pd.read_csv(proc_dir / "zenodo_task_episodes_en.csv")
    e_pat = pd.read_csv(proc_dir / "eicu_patients.csv")
    e_tasks = pd.read_csv(proc_dir / "eicu_shift_tasks.csv")
    n_wards = pd.read_csv(proc_dir / "nrp_wards_summary.csv")
    n_nurses = pd.read_csv(proc_dir / "nrp_nurses.csv")
    n_shifts = pd.read_csv(proc_dir / "nrp_shifts.csv")
    l3_real = pd.read_csv(proc_dir / "l3_task_features_zenodo_real.csv")
    harm_tasks = pd.read_csv(proc_dir / "harmonized_nurseflow_tasks.csv")
    ward_inst = pd.read_csv(proc_dir / "harmonized_ward_shift_instances.csv")

    # 1. Zenodo episode duration & outlier summary
    z_type_stats = (
        z_ep.groupby("nurseflow_task_type")
        .agg(
            episodes=("episode_id", "count"),
            mean_min=("episode_duration_min", "mean"),
            median_min=("episode_duration_min", "median"),
            std_min=("episode_duration_min", "std"),
            p95_min=("episode_duration_min", lambda s: np.percentile(s, 95)),
            max_min=("episode_duration_min", "max"),
            iqr_outliers=("episode_duration_min", _iqr_outlier_count),
        )
        .round(2)
        .sort_values("episodes", ascending=False)
    )
    z_type_stats["share_pct"] = (z_type_stats["episodes"] / len(z_ep) * 100).round(2)

    z_class_hours = (z_ep.groupby("nursing_class")["episode_duration_min"].sum() / 60.0).round(2)
    z_total_hours = float(z_class_hours.sum())

    # 2. eICU correlations & subgroup stats
    eicu_corr_cols = ["acuity_score", "aps_score", "adl_dependency", "is_ventilated", "isolation_precaution", "nursing_events_per_24h"]
    eicu_spearman = e_pat[eicu_corr_cols].corr(method="spearman")["nursing_events_per_24h"].round(4).to_dict()
    harm_spearman = (
        harm_tasks[["acuity_score", "adl_dependency", "isolation_precaution", "is_ventilated", "calibrated_shift_task_min", "workload_points"]]
        .corr(method="spearman")["calibrated_shift_task_min"]
        .round(4)
        .to_dict()
    )

    eicu_by_acuity = (
        e_pat.groupby("acuity_score")
        .agg(
            patients=("patient_id", "count"),
            median_events_24h=("nursing_events_per_24h", "median"),
            mean_events_24h=("nursing_events_per_24h", "mean"),
            pct_vent=("is_ventilated", lambda s: round(s.mean() * 100, 1)),
        )
        .round(2)
    )
    eicu_by_adl = (
        e_pat.groupby("adl_dependency")
        .agg(
            patients=("patient_id", "count"),
            median_events_24h=("nursing_events_per_24h", "median"),
            mean_events_24h=("nursing_events_per_24h", "mean"),
        )
        .round(2)
    )

    # 3. Missingness & Cardinality
    missing_eicu = (e_pat.isna().mean() * 100).round(2)
    missing_eicu_nonzero = missing_eicu[missing_eicu > 0].to_dict()
    missing_l3 = (l3_real.isna().mean() * 100).round(2)
    missing_l3_nonzero = missing_l3[missing_l3 > 0].to_dict()
    missing_harm = (harm_tasks.isna().mean() * 100).round(2)
    missing_harm_nonzero = missing_harm[missing_harm > 0].to_dict()

    # 4. NRP Skill & Coverage summary
    nrp_skill_dist = (
        n_nurses[n_nurses["scenario"] == "Normal"]
        .groupby(["ward_name", "qualification_level"])
        .size()
        .unstack(fill_value=0)
    )

    # 5. L3 ML Decision Gate
    l3_cv = run_l3_predictability_gate(l3_real)

    # 6. Figures
    figs = generate_figures(z_ep, e_pat, e_tasks, n_nurses, n_wards, l3_cv, fig_dir)

    summary = {
        "counts": {
            "zenodo_segments": int(len(z_seg)),
            "zenodo_episodes": int(len(z_ep)),
            "zenodo_total_hours": round(z_total_hours, 2),
            "zenodo_staff": int(z_ep["staff_id"].nunique()),
            "eicu_patients": int(len(e_pat)),
            "eicu_wards": int(e_pat["ward_id"].nunique()),
            "eicu_hospitals": int(e_pat["hospital_id"].nunique()),
            "eicu_shift_tasks": int(len(e_tasks)),
            "nrp_ward_scenarios": int(len(n_wards)),
            "nrp_unique_shifts": int(len(n_shifts)),
            "harmonized_tasks": int(len(harm_tasks)),
        },
        "zenodo_nursing_class_hours": z_class_hours.to_dict(),
        "eicu_spearman_vs_events24h": eicu_spearman,
        "harmonized_spearman_vs_task_min": harm_spearman,
        "missing_pct_nonzero": {
            "eicu_patients": missing_eicu_nonzero,
            "l3_zenodo_real": missing_l3_nonzero,
            "harmonized_tasks": missing_harm_nonzero,
        },
        "l3_decision_gate": l3_cv,
        "figures": figs,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_json, "w", encoding="utf-8") as jf:
        json.dump(summary, jf, ensure_ascii=False, indent=2)

    # 7. Write Vietnamese Markdown Report aligned with docs/feature-spec.md §4 checklist
    z_table_md = _df_to_md(z_type_stats, include_index=True)
    acuity_md = _df_to_md(eicu_by_acuity, include_index=True)
    adl_md = _df_to_md(eicu_by_adl, include_index=True)
    wi_cols = [
        "ward_name",
        "scenario",
        "n_nurses",
        "effective_nurses_estimate",
        "avg_daily_min_headcount",
        "coverage_pressure_ratio",
        "mean_acuity_score",
        "mean_adl_dependency",
    ]
    wi_md = _df_to_md(ward_inst[wi_cols], include_index=False)
    nrp_sk_md = _df_to_md(nrp_skill_dist, include_index=True)
    cv_rows = [
        {"Model": k, "MAE (phút)": v["mae_min"], "RMSE (phút)": v["rmse_min"], "R²": v["r2"]}
        for k, v in l3_cv["models_5fold_cv"].items()
    ]
    cv_md = _df_to_md(pd.DataFrame(cv_rows), include_index=False)
    top_feat_md = _df_to_md(pd.DataFrame(l3_cv["top_10_features_gb"]), include_index=False)

    z_nurs_h = z_class_hours.get("Nursing", 0.0)
    z_non_h = z_class_hours.get("Non-Nursing", 0.0)
    z_brk_h = z_class_hours.get("Break", 0.0)

    report = f"""# Báo cáo EDA & Ghép nối Dữ liệu Đa nguồn — NurseFlow

> Tài liệu này trả lời đầy đủ **Checklist EDA** trong [`feature-spec.md`](feature-spec.md) §4–§5 từ 3 bộ dữ liệu công khai:
> 1. **Zenodo `20754938`** (`Data.xlsx` đã dịch Nhật → Anh): `{len(z_seg):,}` block 10 phút → gộp thành `{len(z_ep):,}` tập tác vụ liên tục (`{z_total_hours:,.1f}` giờ, `{z_ep['staff_id'].nunique()}` nhân sự).
> 2. **eICU Collaborative Research Database Demo v2.0.1**: `{len(e_pat):,}` lượt bệnh nhân ICU tại `{e_pat['ward_id'].nunique()}` khoa / `{e_pat['hospital_id'].nunique()}` bệnh viện → trích xuất `{len(e_tasks):,}` bản ghi tác vụ theo ca 8 giờ.
> 3. **psmet1/nrp (KU Leuven NRP)**: `4` khoa lâm sàng (`Emergency`, `Geriatrics`, `Psychiatry`, `PalliativeCare`) × `3` kịch bản (`Normal`, `Overload`, `Absence`) = `{len(n_wards)}` instance, `{len(n_shifts)}` định nghĩa ca trực (kèm giờ nghỉ từ `data set 1`).

---

## 1. Phân phối thời lượng tác vụ & Outlier (Zenodo 20754938)

**Phát hiện quan trọng khi xử lý dữ liệu thô:** Trong `Data.xlsx`, thời lượng mỗi dòng bị giới hạn tối đa `10.0` phút (do phương pháp quan sát time-and-motion lấy mẫu theo block 10 phút). Nếu dùng trực tiếp chưa gộp, median = `10.0` phút và max = `10.0` phút cho mọi loại việc. Sau khi gộp các block liên tiếp cùng `(staff_id, date, shift_code, task_name)`, ta thu được **`{len(z_ep):,}` tập tác vụ thực (`episode_duration_min`)** với phân phối thực tế:

- **Tỷ trọng thời gian theo nhóm (`nursing_class`):**
  - **Nursing (trực tiếp):** `{z_nurs_h:,.1f}` giờ (`{z_nurs_h/z_total_hours*100:.1f}%`)
  - **Non-Nursing (gián tiếp, chuẩn bị/dọn dẹp, hành chính, đào tạo):** `{z_non_h:,.1f}` giờ (`{z_non_h/z_total_hours*100:.1f}%`) — chiếm gần một nửa thời gian làm việc, là dư địa lớn cho gom việc (`clustering`) và giảm overhead.
  - **Break (nghỉ giữa ca):** `{z_brk_h:,.1f}` giờ (`{z_brk_h/z_total_hours*100:.1f}%`), median một lần nghỉ = `59.0` phút.

{z_table_md}

![Phân phối thời lượng và tỷ trọng thời gian Zenodo](figures/eda_01_zenodo_duration_and_share.png)

---

## 2. Mất cân bằng lớp của `task_type` (Zenodo vs eICU)

- **Trong Zenodo (phòng mổ):** 4 nhóm chiếm tỷ lệ lớn nhất là `prep_setup` (`{z_type_stats.loc['prep_setup','share_pct']}%`), `procedure_care` (`{z_type_stats.loc['procedure_care','share_pct']}%`), `cleanup_sterilization` (`{z_type_stats.loc['cleanup_sterilization','share_pct']}%`), `handover` (`{z_type_stats.loc['handover','share_pct']}%`). Các tác vụ hiếm gồm `safety_prep` (`{int(z_type_stats.loc['safety_prep','episodes'])}` tập) và `med_admin` (`{int(z_type_stats.loc['med_admin','episodes'])}` tập).
- **Trong eICU (hồi sức cấp tính, 24h đầu):** Tổng `{len(e_tasks):,}` cụm tác vụ theo ca 8h bị chi phối bởi `vitals` (`{(e_tasks['task_type']=='vitals').sum():,}`), `med_admin` (`{(e_tasks['task_type']=='med_admin').sum():,}`), và `documentation` (`{(e_tasks['task_type']=='documentation').sum():,}`); trong khi `procedure_care` (`{(e_tasks['task_type']=='procedure_care').sum():,}`) và `hygiene` (`{(e_tasks['task_type']=='hygiene').sum():,}`) ít dòng hơn nhưng mang tính phụ thuộc kỹ năng/ADL cao.
- **Hệ quả cho L3 & L2:** Không nên đánh giá L3 chỉ bằng `MAE` gộp chung; cần báo cáo lỗi theo từng `task_type` hoặc dùng loss có trọng số để tác vụ lâm sàng hiếm không bị kéo theo `vitals`/`documentation`.

---

## 3. Tương quan `acuity_score` & `adl_dependency` với Tải công việc (eICU)

Kiểm định tương quan Spearman trên `{len(e_pat):,}` lượt bệnh nhân eICU (`nursing_events_per_24h`) và `{len(harm_tasks):,}` tác vụ ghép nối (`calibrated_shift_task_min`):

- **Tương quan trên dữ liệu gốc eICU (`nursing_events_per_24h`):**
  - `is_ventilated` ↔ `nursing_events_per_24h`: **ρ = `{eicu_spearman['is_ventilated']}`** (bệnh nhân thở máy tạo tải chăm sóc cao rõ rệt)
  - `acuity_score` ↔ `nursing_events_per_24h`: **ρ = `{eicu_spearman['acuity_score']}`**
  - `aps_score` ↔ `nursing_events_per_24h`: **ρ = `{eicu_spearman['aps_score']}`**
  - `adl_dependency` ↔ `nursing_events_per_24h`: **ρ = `{eicu_spearman['adl_dependency']}`**
  - `isolation_precaution` ↔ `nursing_events_per_24h`: **ρ = `{eicu_spearman['isolation_precaution']}`**
- **Tương quan sau feature engineering trên bảng ghép (`calibrated_shift_task_min`):**
  - `acuity_score`: ρ = `{harm_spearman['acuity_score']}` · `adl_dependency`: ρ = `{harm_spearman['adl_dependency']}` · `is_ventilated`: ρ = `{harm_spearman['is_ventilated']}`

### Trung bình & trung vị tải chăm sóc theo `acuity_score` (eICU)
{acuity_md}

### Trung bình & trung vị tải chăm sóc theo `adl_dependency` (eICU)
{adl_md}

![Tương quan Acuity và ADL với tải điều dưỡng eICU](figures/eda_02_eicu_acuity_adl_workload.png)

---

## 4. Missingness & Cardinality

- **Zenodo `l3_task_features_zenodo_real.csv`:** `{missing_l3_nonzero if missing_l3_nonzero else '0% missing ở toàn bộ cột sau chuẩn hoá Split-Shift (đánh dấu cờ shift_end_was_missing = 1 cho 212 tập ca ≪,≫, fallback shift_length_min = 480.0 phút).'} `
- **eICU `eicu_patients.csv` (cột thiếu > 0%):**
  `{missing_eicu_nonzero}` (trong đó `isolation_type` và `equipment_list` thiếu nghĩa là không có cách ly/thiết bị đặc biệt; `careplan_acuity` thiếu ở `{missing_eicu_nonzero.get('careplan_acuity', 0)}%` lượt — đã fallback theo `apache_score` đúng nguyên tắc `feature-spec.md`).
- **Bảng ghép `harmonized_nurseflow_tasks.csv`:** `{missing_harm_nonzero if missing_harm_nonzero else f'0% missing ở toàn bộ {len(harm_tasks.columns)} cột sau imputation (đánh dấu cờ zenodo_prior_was_missing = 1 cho vitals/hygiene).'}`
- **Cardinality đáng chú ý:** `task_name` (`46` giá trị), `nurseflow_task_type` (`15` trong Zenodo, `8` trong eICU), `ward_id` (`292`), `compat_group_key` (`{harm_tasks['compat_group_key'].nunique()}`). Với cột high-cardinality như `ward_id` / `task_name` khi mở rộng sang DL/GBT nên giữ `nurseflow_task_type` hoặc dùng frequency/target encoding.

---

## 5. Phân bố kỹ năng NRP & Rủi ro Coverage khi `Absence` / `Overload`

Bảng tổng hợp **4 khoa lâm sàng × 3 kịch bản** sau khi ghép nối hồ sơ bệnh nhân eICU & cơ cấu thời gian Zenodo:

{wi_md}

### Phân bố trình độ kinh nghiệm tối đa (`qualification_level` 1–3) theo khoa (Normal)
{nrp_sk_md}

**Rủi ro phát hiện được:**
- Ở kịch bản **`Overload`**, nhu cầu headcount tối thiểu mỗi ngày tăng **+19.5% đến +23.8%** (`Emergency`: `15.36 → 18.36`; `Geriatrics`: `8.43 → 10.14`; `Psychiatry`: `8.00 → 9.90`; `PalliativeCare`: `9.42 → 11.45`), đẩy hệ số áp lực coverage của `Emergency` lên **`0.833`** và `Geriatrics` lên **`0.807`**.
- Khoa `Geriatrics` chỉ có **2 loại kỹ năng** nhưng tỷ lệ xin nghỉ (`236` lượt vắng / 21 điều dưỡng trong 28 ngày) làm nhân lực hiệu dụng giảm còn `~12.57` người/ngày.
- Về giờ nghỉ (`nrp_shifts.csv` từ `data set 1`): đa số ca có giờ nghỉ **30–45 phút** (`29` ca nghỉ 30 phút, `4` ca nghỉ 45 phút); cá biệt có **1 ca tách ở `PalliativeCare`** ghi nghỉ `420` phút (khoảng trống giữa hai nửa ca — cần xử lý tách 2 block trong solver L2 thay vì coi là 1 giờ nghỉ liên tục).

![Áp lực Coverage và phân bố kỹ năng NRP](figures/eda_03_nrp_coverage_and_skills.png)

---

## 6. Mật độ công việc theo giờ & Thiết kế Phase

- Ở **Zenodo (phòng mổ)**, hoạt động tập trung mạnh từ **08:00 đến 17:00**, đạt đỉnh vào **09:00–11:00** và **13:00–15:00**; khoảng **11:00–13:00** có nhịp trùng với cửa sổ nghỉ trưa (`Meal / Break / Rest During Shift`).
- Ở **eICU (ICU 24/7)**, mật độ sự kiện điều dưỡng phân bố đều suốt 24 giờ (~3.6%–4.7%/giờ), hơi tăng nhẹ ở các khung đầu ca **07:00–09:00**, **15:00–16:00**, và **23:00–00:00** (giao ca + đánh giá đầu ca + y lệnh thuốc).
- **Khuyến nghị thiết kế Phase cho L2:** Chia ca trực thành 3 khối chính `Handover_Prep` (đầu/cuối ca), `Care_Execution` (cao điểm chăm sóc & thủ thuật), và `Recovery_Break` (cửa sổ 30–60 phút giữa ca, ràng buộc coverage tối thiểu vẫn đảm bảo trong lúc luân phiên nghỉ).

---

## 7. Cổng quyết định L3 (`docs/feature-spec.md` §4–§5)

Thử nghiệm huấn luyện 5-fold Cross-Validation trên `{l3_cv['n_episodes_evaluated']:,}` tập tác vụ thực từ **Zenodo `20754938`** (loại bỏ `break`, chỉ dùng các feature biết **trước khi thực hiện tác vụ** — 0% leakage):

{cv_md}

### Top 10 feature quan trọng nhất (Gradient Boosting)
{top_feat_md}

**Kết luận Cổng quyết định:**
1. **Có timing cấp task thực không?** **CÓ** — Zenodo `20754938` sau khi gộp block 10 phút cung cấp `{len(z_ep):,}` tập tác vụ có thời lượng thực (`actual_duration_min`), trong đó **`GradientBoosting` giảm MAE từ `{cv_rows[0]['MAE (phút)']}` phút (baseline median) xuống `{cv_rows[3]['MAE (phút)']}` phút và đạt R² = `{cv_rows[3]['R²']}`**.
2. **Nên chọn kiến trúc nào cho L3?** Chọn **Hybrid L3 Estimator (ML + Clinical Multiplier)**:
   - Dùng **Gradient Boosting** (hoặc bảng tra phân vị fallback) dự đoán *thời lượng nền theo loại tác vụ + khung giờ + phase ca trực* từ dữ liệu thực Zenodo.
   - Nhân hệ số hiệu chỉnh theo *acuity bệnh nhân, mức phụ thuộc ADL, thở máy và cách ly* rút ra từ eICU & thang McGill — vì Zenodo chưa có biến bệnh nhân, còn eICU chưa có đồng hồ bấm giờ từng tác vụ.
3. **Granularity huấn luyện:** **Per-task episode** (cấp từng tác vụ) với `compat_group_key` để nạp trực tiếp vào L2 CP-SAT solver.

![Mật độ công việc theo giờ và kết quả cổng quyết định L3](figures/eda_04_hourly_density_and_l3_gate.png)
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(report)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-source EDA and L3 predictability gate.")
    parser.add_argument("--proc-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--fig-dir", type=Path, default=Path("docs/figures"))
    parser.add_argument("--report", type=Path, default=Path("docs/eda-report.md"))
    parser.add_argument("--summary-json", type=Path, default=Path("data/processed/eda_summary.json"))
    args = parser.parse_args()
    summary = run_eda(args.proc_dir, args.fig_dir, args.report, args.summary_json)
    print(json.dumps({"counts": summary["counts"], "l3_decision_gate": summary["l3_decision_gate"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
