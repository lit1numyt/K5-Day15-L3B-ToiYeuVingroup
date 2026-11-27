"""Harmonize Zenodo 20754938, eICU Demo v2.0.1, and psmet1/nrp into NurseFlow ML & solver datasets.

Follows docs/feature-spec.md §1–§2 with strict leakage protection:
1. l3_task_features_zenodo_real.csv: real empirical task-duration regression dataset (2,390 episodes
   from Zenodo 20754938, joined with eICU shift-intensity & NRP ward-shift context priors).
2. harmonized_nurseflow_tasks.csv: full-schema 3-source task table combining eICU patient acuity/ADL/tasks,
   NRP ward/nurse/coverage/break constraints, and Zenodo empirical duration baselines.
3. harmonized_ward_shift_instances.csv: ward-shift orchestration summary ready for L2 CP-SAT & L4 baseline.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


def _assign_shift_phase(hour: int) -> str:
    """Map hour_of_day (0..23) into NurseFlow 5-phase shift structure (Problem-Gap-Solution §3.3)."""
    if hour in {6, 7, 14, 15, 22, 23}:
        return "Handover_Prep"
    if hour in {11, 12, 19, 20, 2, 3}:
        return "Recovery_Break"
    return "Care_Execution"


def _map_eicu_row_to_nrp_ward(unittype: str, age: float | object) -> str:
    """Map eICU ICU unit types + age cohort to the 4 clinical ward archetypes from psmet1/nrp."""
    u = str(unittype)
    if any(k in u for k in ("SICU", "CTICU", "CSICU", "CCU", "Cardiac")):
        return "Emergency"
    if "Neuro" in u:
        return "Psychiatry"
    if "MICU" in u:
        return "PalliativeCare"
    try:
        if pd.notna(age) and float(age) >= 75.0:
            return "Geriatrics"
    except (TypeError, ValueError):
        pass
    return "Emergency"


def build_harmonized_datasets(proc_dir: Path) -> dict:
    """Join Zenodo, eICU, and NRP processed tables and engineer NurseFlow features."""
    z_ep = pd.read_csv(proc_dir / "zenodo_task_episodes_en.csv")
    e_pat = pd.read_csv(proc_dir / "eicu_patients.csv")
    e_tasks = pd.read_csv(proc_dir / "eicu_shift_tasks.csv")
    n_wards = pd.read_csv(proc_dir / "nrp_wards_summary.csv")
    n_nurses = pd.read_csv(proc_dir / "nrp_nurses.csv")
    n_shifts = pd.read_csv(proc_dir / "nrp_shifts.csv")
    n_cov = pd.read_csv(proc_dir / "nrp_coverage_rules.csv")

    # ------------------------------------------------------------------
    # 1) Empirical L3 dataset on REAL Zenodo durations (zero leakage)
    # ------------------------------------------------------------------
    z = z_ep.copy()
    z = z.sort_values(["staff_id", "date", "episode_start_min_of_day"]).reset_index(drop=True)

    # Cyclical time-of-day encoding (feature-spec.md §2)
    z["time_of_day_sin"] = np.sin(2 * np.pi * z["hour_of_day"] / 24.0).round(6)
    z["time_of_day_cos"] = np.cos(2 * np.pi * z["hour_of_day"] / 24.0).round(6)
    z["shift_phase"] = z["hour_of_day"].apply(_assign_shift_phase)
    z["is_handover_window"] = z["hour_of_day"].isin({7, 8, 15, 16, 23, 0}).astype(int)
    z["is_weekend"] = z["day_of_week"].isin({"Saturday", "Sunday"}).astype(int)

    # Shift band aligned across datasets
    z["shift_window"] = z["hour_of_day"].apply(
        lambda h: "Day" if 7 <= h < 15 else ("Evening" if 15 <= h < 23 else "Night")
    )

    # Prior staff workload context computed strictly from earlier days (zero leakage for target)
    staff_type_prior = (
        z.groupby(["staff_id", "nurseflow_task_type"])["episode_id"]
        .cumcount()
        .rename("staff_prior_task_type_count")
    )
    z["staff_prior_task_type_count"] = staff_type_prior
    z["shift_length_min_clean"] = pd.to_numeric(z["shift_length_min"], errors="coerce").fillna(480.0)

    # Enrich with hourly clinical demand density prior from eICU
    eicu_hourly_prior = (
        e_tasks.groupby("hour_of_day", as_index=False)
        .agg(
            eicu_hourly_mean_acuity=("acuity_score", "mean"),
            eicu_hourly_mean_adl=("adl_dependency", "mean"),
            eicu_hourly_task_events=("event_count", "mean"),
        )
        .round(3)
    )
    z = z.merge(eicu_hourly_prior, on="hour_of_day", how="left")

    # Enrich with NRP Emergency ward shift-band capacity/break context
    nrp_band_prior = (
        n_shifts[n_shifts["ward_name"] == "Emergency"]
        .groupby("shift_band", as_index=False)
        .agg(
            nrp_band_job_min=("job_min", "mean"),
            nrp_band_break_min=("break_duration_min", "mean"),
        )
        .round(2)
    )
    z = z.merge(nrp_band_prior, left_on="shift_window", right_on="shift_band", how="left").drop(columns=["shift_band"])
    z["nrp_band_job_min"] = z["nrp_band_job_min"].fillna(480.0)
    z["nrp_band_break_min"] = z["nrp_band_break_min"].fillna(30.0)

    # Target columns (never used as features)
    z = z.rename(columns={"episode_duration_min": "actual_duration_min"})
    z["workload_points"] = (z["actual_duration_min"] / 15.0 * (1.0 + 0.15 * (z["eicu_hourly_mean_acuity"] - 2.5))).round(3)

    l3_real_path = proc_dir / "l3_task_features_zenodo_real.csv"
    z.to_csv(l3_real_path, index=False)

    # ------------------------------------------------------------------
    # 2) Task-type empirical duration priors from Zenodo 20754938
    # ------------------------------------------------------------------
    # Map eICU task_types to matching Zenodo task duration baselines
    z_non_break = z[z["nurseflow_task_type"] != "break"]
    type_dur_stats = (
        z_non_break.groupby("nurseflow_task_type", as_index=False)
        .agg(
            zenodo_n_episodes=("episode_id", "count"),
            zenodo_median_min=("actual_duration_min", "median"),
            zenodo_mean_min=("actual_duration_min", "mean"),
            zenodo_iqr_min=("actual_duration_min", lambda s: float(np.percentile(s, 75) - np.percentile(s, 25))),
        )
        .round(2)
    )
    # Fallback overall clinical nursing median if rare type
    overall_med = float(z_non_break["actual_duration_min"].median())

    # ------------------------------------------------------------------
    # 3) Full 3-dataset harmonized NurseFlow task table (eICU x NRP x Zenodo)
    # ------------------------------------------------------------------
    e_pat_arch = e_pat[["patient_id", "age"]].copy()
    t = e_tasks.merge(e_pat_arch, on="patient_id", how="left")
    t["nrp_ward_archetype"] = t.apply(lambda r: _map_eicu_row_to_nrp_ward(r["care_category"], r["age"]), axis=1)
    t = t.drop(columns=["age"])

    # Ward census from eICU (unique patient stays per hospital_id & ward_id)
    ward_census = (
        e_pat.groupby(["hospital_id", "ward_id"], as_index=False)["patient_id"]
        .nunique()
        .rename(columns={"patient_id": "ward_historical_patients"})
    )
    # Shift census proxy: unique patients active in same ward & shift_block
    shift_census = (
        t.groupby(["ward_id", "shift_block_8h"], as_index=False)["patient_id"]
        .nunique()
        .rename(columns={"patient_id": "census"})
    )
    t = t.merge(ward_census, on=["hospital_id", "ward_id"], how="left")
    t = t.merge(shift_census, on=["ward_id", "shift_block_8h"], how="left")

    # Join Zenodo empirical timing priors by nurseflow_task_type
    t = t.merge(
        type_dur_stats.rename(columns={"nurseflow_task_type": "task_type"}),
        on="task_type",
        how="left",
    )
    t["zenodo_median_min"] = t["zenodo_median_min"].fillna(overall_med)
    t["zenodo_mean_min"] = t["zenodo_mean_min"].fillna(overall_med)

    # Join NRP ward staffing & skill-level stats (Normal scenario baseline + Overload + Absence metrics)
    nrp_ward_normal = n_wards[n_wards["scenario"] == "Normal"][
        ["ward_name", "n_nurses", "avg_daily_min_headcount", "avg_shift_job_min", "avg_break_min"]
    ].rename(
        columns={
            "ward_name": "nrp_ward_archetype",
            "n_nurses": "nrp_ward_total_nurses",
            "avg_daily_min_headcount": "nrp_daily_min_headcount",
            "avg_shift_job_min": "nrp_shift_capacity_min",
            "avg_break_min": "nrp_break_policy_min",
        }
    )
    nrp_nurse_stats = (
        n_nurses[n_nurses["scenario"] == "Normal"]
        .groupby("ward_name", as_index=False)
        .agg(
            nrp_mean_qualification_level=("qualification_level", "mean"),
            nrp_mean_skills_per_nurse=("n_skills", "mean"),
        )
        .rename(columns={"ward_name": "nrp_ward_archetype"})
        .round(2)
    )
    t = t.merge(nrp_ward_normal, on="nrp_ward_archetype", how="left")
    t = t.merge(nrp_nurse_stats, on="nrp_ward_archetype", how="left")

    # Engineer NurseFlow features per docs/feature-spec.md §1–§2
    skill_level_map = {
        "charting": 1,
        "monitoring": 1,
        "basic_care": 1,
        "ward_safety": 1,
        "clinical_assess": 2,
        "iv_med": 2,
        "icu_airway": 3,
        "iv_titration": 3,
    }
    t["required_skill_level"] = t["required_skill"].map(skill_level_map).fillna(2).astype(int)
    t["prep_required"] = t["task_type"].isin({"med_admin", "procedure_care", "hygiene", "safety_prep"}).astype(int)
    t["frequency_band"] = np.where(t["event_count"] >= 6, "recurring_high", np.where(t["event_count"] >= 2, "recurring_mod", "single"))
    t["time_of_day_sin"] = np.sin(2 * np.pi * t["hour_of_day"] / 24.0).round(6)
    t["time_of_day_cos"] = np.cos(2 * np.pi * t["hour_of_day"] / 24.0).round(6)
    t["shift_phase"] = t["hour_of_day"].apply(_assign_shift_phase)
    t["is_handover_window"] = t["hour_of_day"].isin({7, 8, 15, 16, 23, 0}).astype(int)
    t["compat_group_key"] = (
        t["nrp_ward_archetype"] + "|" + t["care_category"].str.replace(" ", "_") + "|" + t["required_skill"]
    )
    t["experience_years_ward_avg"] = (t["nrp_mean_qualification_level"] * 3.0).round(1)
    t["skill_match_rate_proxy"] = (t["nrp_mean_qualification_level"] >= t["required_skill_level"]).astype(int)

    # Calibrated duration & McGill-inspired workload points (explicitly labeled as calibrated proxy)
    acuity_mult = 1.0 + 0.12 * (t["acuity_score"] - 3.0)
    adl_mult = 1.0 + 0.10 * (t["adl_dependency"] - 2.0)
    iso_add_min = 6.0 * t["isolation_precaution"]
    vent_mult = np.where(t["is_ventilated"] == 1, 1.15, 1.0)
    # Combine single-event Zenodo duration baseline + repeated events within 8h shift (sublinear batching factor)
    batch_factor = np.where(t["task_type"].isin({"vitals", "documentation"}), np.sqrt(t["event_count"]), np.minimum(t["event_count"], 4) ** 0.7)
    t["est_single_event_min"] = (t["zenodo_median_min"] * acuity_mult * adl_mult * vent_mult + iso_add_min).clip(lower=2.0).round(2)
    # Note: for high-frequency vitals/charting in ICU flowsheets, scale to realistic shift bundle time
    raw_unit_min = np.where(t["task_type"].isin({"vitals", "documentation"}), 4.0, t["zenodo_median_min"] * 0.45)
    t["calibrated_shift_task_min"] = (raw_unit_min * batch_factor * acuity_mult * adl_mult * vent_mult + iso_add_min).clip(lower=3.0, upper=180.0).round(2)
    t["workload_points"] = (t["calibrated_shift_task_min"] / 15.0 * (1.0 + 0.15 * t["priority"])).round(3)

    harm_tasks_path = proc_dir / "harmonized_nurseflow_tasks.csv"
    t.to_csv(harm_tasks_path, index=False)

    # ------------------------------------------------------------------
    # 4) Ward-shift orchestration benchmark instances (for L2 CP-SAT & L4)
    # ------------------------------------------------------------------
    eicu_by_arch = (
        e_pat.assign(
            nrp_ward_archetype=e_pat.apply(lambda r: _map_eicu_row_to_nrp_ward(r["care_category"], r["age"]), axis=1)
        )
        .groupby("nrp_ward_archetype", as_index=False)
        .agg(
            eicu_patients_count=("patient_id", "count"),
            mean_acuity_score=("acuity_score", "mean"),
            mean_adl_dependency=("adl_dependency", "mean"),
            pct_ventilated=("is_ventilated", "mean"),
            pct_isolation=("isolation_precaution", "mean"),
        )
        .round(3)
    )
    inst = n_wards.merge(eicu_by_arch, left_on="ward_name", right_on="nrp_ward_archetype", how="left")
    inst["effective_nurses_estimate"] = (
        inst["n_nurses"] * (1.0 - inst["n_absence_requests"] / (inst["n_nurses"] * inst["period_days"]).clip(lower=1))
    ).round(2)
    inst["coverage_pressure_ratio"] = (
        inst["avg_daily_min_headcount"] / inst["effective_nurses_estimate"].clip(lower=1)
    ).round(3)

    # Merge empirical nursing time share from Zenodo
    z_class_share = z_ep.groupby("nursing_class")["episode_duration_min"].sum()
    total_z_min = float(z_class_share.sum())
    inst["zenodo_direct_nursing_share"] = round(float(z_class_share.get("Nursing", 0.0)) / total_z_min, 4)
    inst["zenodo_non_nursing_share"] = round(float(z_class_share.get("Non-Nursing", 0.0)) / total_z_min, 4)
    inst["zenodo_break_share"] = round(float(z_class_share.get("Break", 0.0)) / total_z_min, 4)

    inst_path = proc_dir / "harmonized_ward_shift_instances.csv"
    inst.to_csv(inst_path, index=False)

    return {
        "l3_real_rows": int(len(z)),
        "l3_real_cols": int(len(z.columns)),
        "harmonized_tasks_rows": int(len(t)),
        "harmonized_tasks_cols": int(len(t.columns)),
        "ward_instances_rows": int(len(inst)),
        "files": [str(l3_real_path), str(harm_tasks_path), str(inst_path)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Harmonize Zenodo, eICU, and NRP into NurseFlow feature tables.")
    parser.add_argument("--proc-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    res = build_harmonized_datasets(args.proc_dir)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
