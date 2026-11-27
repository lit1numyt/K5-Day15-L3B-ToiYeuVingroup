"""Build deterministic, explicitly synthetic shared inputs for CP3 module work."""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path


def build_handoff(root, output):
    fixtures = root / "data/cp2-cases.json"
    reference_path = root / "data/reference/ward_task_duration.csv"
    base = next(case["input"] for case in json.loads(fixtures.read_text(encoding="utf-8")) if case["id"] == "F03")
    with reference_path.open(newline="", encoding="utf-8") as stream:
        reference = {row["task_type"]: row for row in csv.DictReader(stream)}
    task_types = ["med_admin", "vitals", "wound_care", "lab_collection", "iv_care", "catheter_care"]
    base = copy.deepcopy(base)
    # Every policy/roster/taxonomy value here is a declared integration fixture.
    base["shift"]["coverage_rules"][0]["min_staff"] = 1
    base["shift"]["census"] = len(base["patients"])
    base["request"]["text"] = (
        "Kịch bản kỹ thuật tại khoa ACE. Task theo định nghĩa của bảng nguồn, "
        "mỗi task thực hiện bởi một staff theo điều kiện được khai báo của kịch bản. "
        "Tạo bản nháp theo roster và ràng buộc đã cung cấp."
    )
    for nurse, years in zip(base["nurses"], [1, 4, 8]):
        nurse.update(skills=task_types.copy(), qualification_level=2,
                     experience_years=years, specialization="acute_ward_demo")
    for index, patient in enumerate(base["patients"]):
        patient.update(acuity_score=[1, 3, 5][index % 3],
                       adl_dependency=[1, 2, 4][index % 3],
                       care_category="medical", isolation_precaution=index == 2)
    for task, kind in zip(base["tasks"], task_types):
        task.update(task_type=kind, required_skill=[kind], required_skill_level=1,
                    priority=1, frequency="once", duration_source="given")

    cases = []
    for case_id, purpose in [
        ("P01", "given_duration"),
        ("P02", "mixed_given_and_lookup"),
        ("P03", "absent_nurse_with_same_coverage_policy"),
    ]:
        instance = copy.deepcopy(base)
        if case_id != "P01":
            for task in instance["tasks"][1:]:
                task["est_duration_min"] = math.ceil(float(reference[task["task_type"]]["mean_duration_min"]))
                task["duration_source"] = "lookup:simmons-2025-table3"
        if case_id == "P03":
            instance["nurses"] = [n for n in instance["nurses"] if n["nurse_id"] != "N3"]
        l3_input = copy.deepcopy(instance)
        for task in l3_input["tasks"]:
            if task["duration_source"].startswith("lookup:"):
                del task["est_duration_min"]
                del task["duration_source"]
        case = {"id": case_id, "purpose": purpose,
                "instance": instance, "l3_input": l3_input}
        if case_id == "P03":
            case["absent_nurse_id"] = "N3"
        cases.append(case)

    bundle = {
        "data_kind": "synthetic",
        "generation": "deterministic; no random sampling",
        "seed": None,
        "owner": "Lam; based on data research with Kien; Codex assists",
        "scope": "CP3 module integration inputs",
        "field_provenance": {
            "ids_roster_skills_rooms_windows_breaks_capacity_coverage": "technical assumptions based on F03; min_staff=1 for all cases",
            "qualification_level_required_skill_level": "technical ordinal levels 2/1; not a clinical credential scale",
            "experience_years": "technical examples 1/4/8; independent of qualification level",
            "acuity_score_adl_dependency": "technical ordinal inputs 1/3/5 and 1/2/4; not calibrated clinical scales",
            "care_category_isolation_priority_frequency_census": "declared scenario inputs; census counts fixture patients",
            "duration_source_given": "F03 technical input, 10 minutes per task",
            "duration_source_lookup": "published task mean from Simmons Table 3, rounded up to integer minutes",
        },
        "lookup_conditions": "single-staff example tasks matching the source definition in an ACE-style scenario; patient-specific duration remains unvalidated",
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [fixtures, reference_path]},
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"cases": len(cases), "data_kind": bundle["data_kind"], "output": str(output)}


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "data/preliminary/instances.json")
    args = parser.parse_args()
    print(json.dumps(build_handoff(root, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
