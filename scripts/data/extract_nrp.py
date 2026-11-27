"""Extract nurse profiles, skill/experience levels, shift breaks, absences, and coverage rules from psmet1/nrp."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def _hhmmss_to_min(t: str) -> float:
    """Parse HH:MM:SS(.frac)(+tz) into minutes since midnight."""
    clean = t.split("+")[0].split("-")[0].split(".")[0].strip()
    hh, mm, ss = [int(x) for x in clean.split(":")]
    return round(hh * 60 + mm + ss / 60.0, 2)


def _shift_band(start_min: float) -> str:
    if 300 <= start_min < 720:
        return "Day"
    if 720 <= start_min < 1140:
        return "Evening"
    return "Night"


def _parse_ds1_breaks(ds1_path: Path) -> dict[str, dict]:
    """Read break start/end windows from data set 1 ShiftType definitions."""
    if not ds1_path.exists():
        return {}
    root = ET.parse(ds1_path).getroot()
    breaks: dict[str, dict] = {}
    for st in root.findall(".//ShiftType"):
        sid = (st.findtext("ID") or "").strip()
        b_start = st.findtext("StartTimeBreak")
        b_end = st.findtext("EndTimeBreak")
        if sid and b_start and b_end:
            bs_min = _hhmmss_to_min(b_start)
            be_min = _hhmmss_to_min(b_end)
            dur = round(be_min - bs_min if be_min >= bs_min else be_min - bs_min + 1440.0, 2)
            breaks[sid] = {
                "break_start_time": b_start.split(".")[0],
                "break_end_time": b_end.split(".")[0],
                "break_duration_min": dur,
            }
    return breaks


def extract_nrp(nrp_dir: Path, out_dir: Path) -> dict:
    """Parse data_set_2 clinical XML instances + data_set_1 break timings into CSV tables."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ds2_dir = nrp_dir / "data_set_2" / "Instances"
    ds1_dir = nrp_dir / "data_set_1" / "Input"

    ward_rows: list[dict] = []
    nurse_rows: list[dict] = []
    shift_rows: list[dict] = []
    cov_rows: list[dict] = []
    seen_shifts: set[tuple[str, str]] = set()

    for xml_path in sorted(ds2_dir.glob("ext_New-*.xml")):
        # Example: ext_New-Hospital1-Emergency-Absence.xml
        stem = xml_path.stem.replace("ext_New-", "")
        hospital, ward, scenario = stem.split("-", 2)
        ds1_ward = "Palliative_Care" if ward == "PalliativeCare" else ward
        ds1_path = ds1_dir / f"{hospital}-{ds1_ward}-{scenario}.xml"
        ds1_breaks = _parse_ds1_breaks(ds1_path)

        root = ET.parse(xml_path).getroot()
        period_start = dt.date.fromisoformat(root.findtext("SchedulePeriod/StartDate") or "2007-12-03")
        period_end = dt.date.fromisoformat(root.findtext("SchedulePeriod/EndDate") or "2007-12-30")
        n_days = (period_end - period_start).days + 1

        # Skill types & SkillTypeSets
        skill_ids = [el.text.strip() for el in root.findall(".//SkillTypes/SkillType/SkillTypeId") if el.text]
        skill_sets: dict[str, list[str]] = {}
        for ss in root.findall(".//SkillTypeSets/SkillTypeSet"):
            ssid = (ss.findtext("SkillTypeSetId") or "").strip()
            skill_sets[ssid] = [x.text.strip() for x in ss.findall("SkillTypeId") if x.text]

        # Shift types & ShiftTypeSets
        shift_map: dict[str, dict] = {}
        for st in root.findall(".//ShiftTypes/ShiftTypeData"):
            sid = (st.findtext("ShiftTypeId") or "").strip()
            s_time = (st.findtext("StartTime") or "00:00:00").strip()
            e_time = (st.findtext("EndTime") or "00:00:00").strip()
            job_min = round(float(st.findtext("JobTime") or 0) / 60.0, 2)
            rb_min = round(float(st.findtext("RestTimeBefore") or 0) / 60.0, 2)
            ra_min = round(float(st.findtext("RestTimeAfter") or 0) / 60.0, 2)
            brk = ds1_breaks.get(sid, {"break_start_time": "", "break_end_time": "", "break_duration_min": 0.0})
            row = {
                "hospital": hospital,
                "ward_name": ward,
                "shift_id": sid,
                "start_time": s_time,
                "end_time": e_time,
                "shift_band": _shift_band(_hhmmss_to_min(s_time)),
                "job_min": job_min,
                "rest_before_min": rb_min,
                "rest_after_min": ra_min,
                "break_start_time": brk["break_start_time"],
                "break_end_time": brk["break_end_time"],
                "break_duration_min": brk["break_duration_min"],
            }
            shift_map[sid] = row
            if (ward, sid) not in seen_shifts:
                seen_shifts.add((ward, sid))
                shift_rows.append(row)

        shift_sets: dict[str, list[str]] = {}
        for sts in root.findall(".//ShiftTypeSets/ShiftTypeSet"):
            stsid = (sts.findtext("ShiftTypeSetId") or "").strip()
            shift_sets[stsid] = [x.text.strip() for x in sts.findall("ShiftTypeId") if x.text]

        # Employees (nurses)
        emps = root.findall(".//Employees/EmployeeData")
        total_absences = 0
        for emp in emps:
            eid = (emp.findtext("EmployeeId") or "").strip()
            sk_pairs = []
            for est in emp.findall("EmployeeSkillTypesSet/EmployeeSkillType"):
                sk_id = (est.findtext("SkillTypeId") or "").strip()
                lvl = int(est.findtext("LevelOfExperience") or 1)
                wt = int(est.findtext("Weight") or 0)
                sk_pairs.append({"skill_id": sk_id, "level": lvl, "weight": wt})
            max_lvl = max((x["level"] for x in sk_pairs), default=1)
            avg_lvl = round(sum(x["level"] for x in sk_pairs) / len(sk_pairs), 2) if sk_pairs else 1.0
            abs_reqs = emp.findall("Requests/AbsenceRequest")
            total_absences += len(abs_reqs)
            nurse_rows.append(
                {
                    "hospital": hospital,
                    "ward_name": ward,
                    "scenario": scenario,
                    "nurse_id": f"NRP_{eid}",
                    "n_skills": len(sk_pairs),
                    "skills": "|".join(x["skill_id"] for x in sk_pairs),
                    "qualification_level": max_lvl,
                    "avg_experience_level": avg_lvl,
                    "skill_levels_json": json.dumps(sk_pairs),
                    "n_absence_requests": len(abs_reqs),
                    "absence_ratio": round(len(abs_reqs) / max(n_days, 1), 3),
                }
            )

        # Coverage requirements
        reqs = root.findall(".//ScheduleRequirements/ScheduleRequirementData")
        sum_min = 0
        sum_max = 0
        for req in reqs:
            r_date = (req.findtext("Date") or "").strip()
            sk_set = (req.findtext("SkillTypeSetId") or "").strip()
            req_lvl = int(req.findtext("LevelOfExperience") or 1)
            sh_set = (req.findtext("ShiftTypeSetId") or "").strip()
            r_min = int(req.findtext("Threshold/Interval/Min") or 0)
            r_max = int(req.findtext("Threshold/Interval/Max") or r_min)
            wt = int(req.findtext("Weight") or 0)
            sum_min += r_min
            sum_max += r_max
            resolved_shifts = shift_sets.get(sh_set, [])
            resolved_skills = skill_sets.get(sk_set, [sk_set])
            cov_rows.append(
                {
                    "hospital": hospital,
                    "ward_name": ward,
                    "scenario": scenario,
                    "date": r_date,
                    "skill_set_id": sk_set,
                    "resolved_skills": "|".join(resolved_skills),
                    "required_skill_level": req_lvl,
                    "shift_set_id": sh_set,
                    "resolved_shifts": "|".join(resolved_shifts),
                    "min_nurses": r_min,
                    "max_nurses": r_max,
                    "weight": wt,
                }
            )

        avg_job = round(sum(s["job_min"] for s in shift_map.values()) / max(len(shift_map), 1), 2)
        brk_vals = [s["break_duration_min"] for s in shift_map.values() if s["break_duration_min"] > 0]
        avg_brk = round(sum(brk_vals) / max(len(brk_vals), 1), 2) if brk_vals else 0.0
        ward_rows.append(
            {
                "hospital": hospital,
                "ward_name": ward,
                "scenario": scenario,
                "period_days": n_days,
                "n_nurses": len(emps),
                "n_shift_types": len(shift_map),
                "n_skill_types": len(skill_ids),
                "n_absence_requests": total_absences,
                "n_coverage_rules": len(reqs),
                "total_min_required_shifts": sum_min,
                "total_max_required_shifts": sum_max,
                "avg_daily_min_headcount": round(sum_min / max(n_days, 1), 2),
                "avg_shift_job_min": avg_job,
                "avg_break_min": avg_brk,
            }
        )

    def _write(path: Path, rows: list[dict]) -> str:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return str(path)

    return {
        "wards_rows": len(ward_rows),
        "nurses_rows": len(nurse_rows),
        "shifts_rows": len(shift_rows),
        "coverage_rows": len(cov_rows),
        "wards_csv": _write(out_dir / "nrp_wards_summary.csv", ward_rows),
        "nurses_csv": _write(out_dir / "nrp_nurses.csv", nurse_rows),
        "shifts_csv": _write(out_dir / "nrp_shifts.csv", shift_rows),
        "coverage_csv": _write(out_dir / "nrp_coverage_rules.csv", cov_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract structured tables from data/nrp clinical instances.")
    parser.add_argument("--nrp-dir", type=Path, default=Path("data/nrp"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    res = extract_nrp(args.nrp_dir, args.out_dir)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
