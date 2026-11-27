"""Extract patient acuity, ADL dependency, clinical flags, and nursing care task demand from eICU Demo v2.0.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _clean_age(val: object) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if s.startswith(">"):
        return 90.0
    try:
        return float(s)
    except ValueError:
        return np.nan


def _parse_hhmm_to_hour(t: object) -> float:
    if pd.isna(t):
        return 8.0
    parts = str(t).strip().split(":")
    try:
        return int(parts[0]) + int(parts[1]) / 60.0
    except (ValueError, IndexError):
        return 8.0


def extract_eicu(eicu_dir: Path, out_dir: Path) -> dict:
    """Build eicu_patients.csv and eicu_shift_tasks.csv from eICU Demo v2.0.1 tables."""
    out_dir.mkdir(parents=True, exist_ok=True)

    pat = pd.read_csv(eicu_dir / "patient.csv.gz", compression="gzip")
    hosp = pd.read_csv(eicu_dir / "hospital.csv.gz", compression="gzip")
    apache_res = pd.read_csv(eicu_dir / "apachePatientResult.csv.gz", compression="gzip")
    apache_var = pd.read_csv(eicu_dir / "apacheApsVar.csv.gz", compression="gzip")
    cpg = pd.read_csv(eicu_dir / "carePlanGeneral.csv.gz", compression="gzip")
    ncare = pd.read_csv(eicu_dir / "nurseCare.csv.gz", compression="gzip", low_memory=False)
    nassess = pd.read_csv(eicu_dir / "nurseAssessment.csv.gz", compression="gzip", low_memory=False)
    med = pd.read_csv(eicu_dir / "medication.csv.gz", compression="gzip", low_memory=False)
    inf = pd.read_csv(eicu_dir / "infusiondrug.csv.gz", compression="gzip", low_memory=False)
    treat = pd.read_csv(eicu_dir / "treatment.csv.gz", compression="gzip", low_memory=False)
    io_df = pd.read_csv(eicu_dir / "intakeOutput.csv.gz", compression="gzip", low_memory=False)
    nchart = pd.read_csv(
        eicu_dir / "nurseCharting.csv.gz",
        compression="gzip",
        usecols=["patientunitstayid", "nursingchartoffset", "nursingchartcelltypecat", "nursingchartcelltypevallabel"],
        low_memory=False,
    )

    # Deduplicate apachePatientResult: prefer IVa over IV when both exist
    apache_res["ver_rank"] = apache_res["apacheversion"].map({"IVa": 0, "IV": 1}).fillna(2)
    apache_best = (
        apache_res.sort_values(["patientunitstayid", "ver_rank"])
        .drop_duplicates("patientunitstayid")
        .loc[
            :,
            [
                "patientunitstayid",
                "acutephysiologyscore",
                "apachescore",
                "actualiculos",
                "actualventdays",
                "actualhospitalmortality",
            ],
        ]
    )

    # carePlanGeneral: latest acuity, ventilation, care limitation
    cpg_acuity = (
        cpg[cpg["cplgroup"] == "Acuity"]
        .sort_values(["patientunitstayid", "cplitemoffset"])
        .drop_duplicates("patientunitstayid", keep="last")
        .rename(columns={"cplitemvalue": "careplan_acuity"})[["patientunitstayid", "careplan_acuity"]]
    )
    cpg_vent = (
        cpg[cpg["cplgroup"] == "Ventilation"]
        .sort_values(["patientunitstayid", "cplitemoffset"])
        .drop_duplicates("patientunitstayid", keep="last")
        .rename(columns={"cplitemvalue": "ventilation_status"})[["patientunitstayid", "ventilation_status"]]
    )

    # nurseCare derived flags: isolation, ADL dependency, mobility, equipment, restraints
    ncare_iso = (
        ncare[ncare["celllabel"] == "Isolation Precautions"]
        .groupby("patientunitstayid")["cellattributevalue"]
        .agg(lambda s: "|".join(sorted(set(str(x) for x in s.dropna()))))
        .rename("isolation_type")
        .reset_index()
    )

    ncare_hyg = ncare[ncare["celllabel"] == "Hygiene/ADLs"].copy()
    ncare_hyg["adl_val_lower"] = ncare_hyg["cellattributevalue"].astype(str).str.lower()
    hyg_agg = ncare_hyg.groupby("patientunitstayid")["adl_val_lower"].agg(list).reset_index()

    ncare_act = ncare[ncare["celllabel"] == "Activity"].copy()
    ncare_act["act_val_lower"] = ncare_act["cellattributevalue"].astype(str).str.lower()
    act_agg = ncare_act.groupby("patientunitstayid")["act_val_lower"].agg(list).reset_index()

    ncare_eq = (
        ncare[ncare["celllabel"] == "Equipment"]
        .groupby("patientunitstayid")["cellattributevalue"]
        .agg(lambda s: "|".join(sorted(set(str(x) for x in s.dropna()))))
        .rename("equipment_list")
        .reset_index()
    )
    restraint_ids = set(ncare[ncare["celllabel"] == "Restraints"]["patientunitstayid"].unique())

    # Event counts per stay
    cnt_ncare = ncare.groupby("patientunitstayid").size().rename("nurse_care_events")
    cnt_nassess = nassess.groupby("patientunitstayid").size().rename("nurse_assess_events")
    cnt_nchart = nchart.groupby("patientunitstayid").size().rename("nurse_chart_events")
    cnt_med = med[med["drugordercancelled"].astype(str) != "Yes"].groupby("patientunitstayid").size().rename("med_orders")
    cnt_inf = inf.groupby("patientunitstayid").size().rename("iv_infusion_events")
    cnt_treat = treat.groupby("patientunitstayid").size().rename("treatment_events")
    cnt_io = io_df.groupby("patientunitstayid").size().rename("io_events")

    df = pat.merge(hosp, on="hospitalid", how="left")
    df = df.merge(apache_best, on="patientunitstayid", how="left")
    df = df.merge(apache_var[["patientunitstayid", "intubated", "vent", "dialysis"]], on="patientunitstayid", how="left")
    df = df.merge(cpg_acuity, on="patientunitstayid", how="left")
    df = df.merge(cpg_vent, on="patientunitstayid", how="left")
    df = df.merge(ncare_iso, on="patientunitstayid", how="left")
    df = df.merge(hyg_agg, on="patientunitstayid", how="left")
    df = df.merge(act_agg, on="patientunitstayid", how="left")
    df = df.merge(ncare_eq, on="patientunitstayid", how="left")

    for s in [cnt_ncare, cnt_nassess, cnt_nchart, cnt_med, cnt_inf, cnt_treat, cnt_io]:
        df = df.merge(s, on="patientunitstayid", how="left")
        df[s.name] = df[s.name].fillna(0).astype(int)

    df["age_num"] = df["age"].apply(_clean_age)
    df["unit_los_min"] = df["unitdischargeoffset"].clip(lower=60).fillna(1440).astype(float)
    df["los_days"] = (df["unit_los_min"] / 1440.0).clip(lower=0.25)
    df["isolation_precaution"] = df["isolation_type"].notna().astype(int)
    df["has_restraints"] = df["patientunitstayid"].isin(restraint_ids).astype(int)
    df["is_ventilated"] = (
        (df["vent"].fillna(0) == 1)
        | (df["intubated"].fillna(0) == 1)
        | df["ventilation_status"].astype(str).str.contains("Ventilated", case=False, na=False)
    ).astype(int)
    df["is_dialysis"] = (df["dialysis"].fillna(0) == 1).astype(int)

    # Derive ADL dependency 1 (low/self) to 4 (total assist / bedrest)
    def compute_adl(row: pd.Series) -> int:
        hyg = row["adl_val_lower"] if isinstance(row["adl_val_lower"], list) else []
        act = row["act_val_lower"] if isinstance(row["act_val_lower"], list) else []
        score = 2
        if any("bedrest" in x or "turn/position" in x for x in act):
            score += 1
        if any("adls assist" in x or "bath" in x or "peri care" in x for x in hyg):
            score += 1
        if any("adls self" in x or "ambulate" in x or "chair" in x for x in hyg + act) and score > 1:
            if "bedrest" not in " ".join(act):
                score -= 1
        if row["is_ventilated"] == 1:
            score = max(score, 3)
        return int(min(4, max(1, score)))

    df["adl_dependency"] = df.apply(compute_adl, axis=1)

    # Derive unified acuity_score (1..5) from APACHE score quantiles + careplan_acuity + organ support
    ap = df["apachescore"].replace(-1, np.nan)
    cp_map = {"Low": 2.0, "Intermediate": 3.0, "High": 4.0}
    cp_score = df["careplan_acuity"].map(cp_map)

    def compute_acuity(idx: int) -> int:
        a = ap.iat[idx]
        c = cp_score.iat[idx]
        v = df["is_ventilated"].iat[idx]
        d = df["is_dialysis"].iat[idx]
        if pd.notna(a):
            if a < 35:
                base = 1
            elif a < 50:
                base = 2
            elif a < 68:
                base = 3
            elif a < 90:
                base = 4
            else:
                base = 5
        elif pd.notna(c):
            base = int(round(c))
        else:
            base = 3
        if v == 1 and base < 4:
            base += 1
        if d == 1 and base < 5:
            base = max(base, 4)
        return int(min(5, max(1, base)))

    df["acuity_score"] = [compute_acuity(i) for i in range(len(df))]
    df["total_nursing_events"] = (
        df["nurse_care_events"]
        + df["nurse_assess_events"]
        + df["nurse_chart_events"]
        + df["med_orders"]
        + df["iv_infusion_events"]
        + df["treatment_events"]
        + df["io_events"]
    )
    df["nursing_events_per_24h"] = (df["total_nursing_events"] / df["los_days"]).round(2)

    patient_out_cols = [
        "patientunitstayid",
        "wardid",
        "hospitalid",
        "region",
        "numbedscategory",
        "unittype",
        "unitstaytype",
        "gender",
        "age_num",
        "unitadmittime24",
        "unit_los_min",
        "apachescore",
        "acutephysiologyscore",
        "careplan_acuity",
        "acuity_score",
        "adl_dependency",
        "is_ventilated",
        "is_dialysis",
        "isolation_precaution",
        "isolation_type",
        "has_restraints",
        "equipment_list",
        "nurse_care_events",
        "nurse_assess_events",
        "nurse_chart_events",
        "med_orders",
        "iv_infusion_events",
        "treatment_events",
        "io_events",
        "total_nursing_events",
        "nursing_events_per_24h",
        "actualhospitalmortality",
    ]
    patients_out = df[patient_out_cols].rename(
        columns={
            "patientunitstayid": "patient_id",
            "wardid": "ward_id",
            "hospitalid": "hospital_id",
            "unittype": "care_category",
            "age_num": "age",
            "apachescore": "apache_score",
            "acutephysiologyscore": "aps_score",
        }
    )
    patients_csv = out_dir / "eicu_patients.csv"
    patients_out.to_csv(patients_csv, index=False)

    # Extract shift-level task demand records across the first 24h (offsets 0..1440 min) per patient
    pat_meta = patients_out.set_index("patient_id")[
        ["ward_id", "care_category", "acuity_score", "adl_dependency", "isolation_precaution", "is_ventilated", "unitadmittime24", "hospital_id"]
    ].copy()
    pat_meta["admit_hour"] = pat_meta["unitadmittime24"].apply(_parse_hhmm_to_hour)

    def build_events(frame: pd.DataFrame, offset_col: str, task_type: str, req_skill: str, priority: int) -> pd.DataFrame:
        sub = frame[(frame[offset_col] >= 0) & (frame[offset_col] < 1440)][["patientunitstayid", offset_col]].copy()
        sub = sub.rename(columns={"patientunitstayid": "patient_id", offset_col: "offset_min"})
        sub["task_type"] = task_type
        sub["required_skill"] = req_skill
        sub["priority"] = priority
        return sub

    # Map eICU clinical logs into NurseFlow task_type taxonomy
    ncare_hyg_ev = build_events(ncare[ncare["celllabel"] == "Hygiene/ADLs"], "nursecareoffset", "hygiene", "basic_care", 2)
    ncare_mob_ev = build_events(ncare[ncare["celllabel"] == "Activity"], "nursecareoffset", "mobilization", "basic_care", 2)
    ncare_saf_ev = build_events(ncare[ncare["celllabel"] == "Safety"], "nursecareoffset", "safety_prep", "ward_safety", 2)
    ncare_trt_ev = build_events(ncare[ncare["celllabel"] == "Treatments"], "nursecareoffset", "procedure_care", "icu_airway", 3)
    nassess_ev = build_events(nassess, "nurseassessoffset", "assessment", "clinical_assess", 3)
    med_ev = build_events(med[med["drugordercancelled"].astype(str) != "Yes"], "drugstartoffset", "med_admin", "iv_med", 3)
    inf_ev = build_events(inf, "infusionoffset", "med_admin", "iv_titration", 4)
    vitals_ev = build_events(nchart[nchart["nursingchartcelltypecat"] == "Vital Signs"], "nursingchartoffset", "vitals", "monitoring", 2)
    doc_ev = build_events(nchart[nchart["nursingchartcelltypecat"] != "Vital Signs"], "nursingchartoffset", "documentation", "charting", 1)

    all_ev = pd.concat(
        [ncare_hyg_ev, ncare_mob_ev, ncare_saf_ev, ncare_trt_ev, nassess_ev, med_ev, inf_ev, vitals_ev, doc_ev],
        ignore_index=True,
    )
    all_ev = all_ev.merge(pat_meta, on="patient_id", how="inner")
    all_ev["hour_of_day"] = ((all_ev["admit_hour"] + all_ev["offset_min"] / 60.0) % 24).astype(int)
    all_ev["shift_window"] = pd.cut(
        all_ev["hour_of_day"],
        bins=[-1, 6, 14, 22, 24],
        labels=["Night", "Day", "Evening", "Night"],
        ordered=False,
    ).astype(str)
    all_ev["shift_block_8h"] = (all_ev["offset_min"] // 480).astype(int)

    # Aggregate to 1 row per (patient_id, shift_block_8h, task_type)
    tasks_agg = (
        all_ev.groupby(["patient_id", "ward_id", "hospital_id", "shift_block_8h", "shift_window", "task_type", "required_skill"], as_index=False)
        .agg(
            hour_of_day=("hour_of_day", "median"),
            event_count=("offset_min", "count"),
            priority=("priority", "max"),
            care_category=("care_category", "first"),
            acuity_score=("acuity_score", "first"),
            adl_dependency=("adl_dependency", "first"),
            isolation_precaution=("isolation_precaution", "first"),
            is_ventilated=("is_ventilated", "first"),
        )
    )
    tasks_agg["hour_of_day"] = tasks_agg["hour_of_day"].round().astype(int) % 24
    tasks_csv = out_dir / "eicu_shift_tasks.csv"
    tasks_agg.to_csv(tasks_csv, index=False)

    return {
        "patients_rows": int(len(patients_out)),
        "shift_tasks_rows": int(len(tasks_agg)),
        "patients_csv": str(patients_csv),
        "shift_tasks_csv": str(tasks_csv),
    }


def main() -> None:
    default_eicu = Path("data/eicu-collaborative-research-database-demo-2.0.1/eicu-collaborative-research-database-demo-2.0.1")
    parser = argparse.ArgumentParser(description="Extract NurseFlow patient and task demand tables from eICU Demo.")
    parser.add_argument("--eicu-dir", type=Path, default=default_eicu)
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    res = extract_eicu(args.eicu_dir, args.out_dir)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
