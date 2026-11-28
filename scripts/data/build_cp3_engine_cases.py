"""Build small deterministic technical cases; values are declared assumptions."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def build_cases(root, output):
    source = root / "data/preliminary/instances.json"
    base = json.loads(source.read_text(encoding="utf-8"))["cases"][0]["instance"]
    cases = []

    def add(cid, purpose, expected, instance):
        instance["request"]["text"] = "Fixture kỹ thuật CP3: " + purpose
        instance["shift"]["census"] = len(instance["patients"])
        cases.append({"id": cid, "purpose": purpose, "expected_status": expected,
                      "instance": instance})

    data = copy.deepcopy(base)
    data["shift"]["break_policy"]["window"] = [60, 90]
    add("C01", "parallel_recovery_with_coverage", "draft", data)

    data = copy.deepcopy(base)
    data["patients"] = data["patients"][:1]
    data["tasks"] = data["tasks"][:3]
    for nurse in data["nurses"]:
        nurse["skills"] = ["A"]
    for task, kind, start, end, duration, predecessor in zip(
        data["tasks"], ["preparation", "care", "handover"],
        [0, 15, 105], [15, 60, 120], [5, 20, 5], [None, "T1", "T2"],
    ):
        task.update(patient_id="P1", task_type=kind, required_skill=["A"],
                    earliest_start=start, deadline=end, est_duration_min=duration,
                    precedence_task_id=predecessor)
    add("C02", "patient_preparation_care_recovery_handover", "draft", data)

    data = copy.deepcopy(base)
    data["tasks"] = data["tasks"][:3]
    data["shift"]["equipment_capacity"] = {"E1": 1}
    for task in data["tasks"]:
        task.update(equipment_required=["E1"], deadline=30)
    add("C03", "one_shared_device_three_ten_minute_tasks", "draft", data)
    impossible = copy.deepcopy(data)
    for task in impossible["tasks"]:
        task["deadline"] = 20
    add("C04", "device_requires_30_minutes_in_20_minute_window", "infeasible", impossible)

    data = copy.deepcopy(base)
    data["nurses"] = data["nurses"][:2]
    data["patients"] = data["patients"][:1]
    data["tasks"] = data["tasks"][:2]
    for nurse, task, skill in zip(data["nurses"], data["tasks"], ["A", "B"]):
        nurse["skills"] = [skill]
        task.update(patient_id="P1", task_type=skill, required_skill=[skill])
    add("C05", "same_patient_needs_two_different_skills", "draft", data)

    data = copy.deepcopy(base)
    data["shift"]["coverage_rules"][0]["min_staff"] = 3
    add("C06", "all_three_staff_required_on_duty_but_breaks_mandatory", "infeasible", data)

    data = copy.deepcopy(base)
    data["nurses"] = data["nurses"][:2]
    data["tasks"] = data["tasks"][:2]
    data["patients"] = data["patients"][:2]
    data["patients"][1]["room"] = "R2"
    for nurse, skill in zip(data["nurses"], ["A", "B"]):
        nurse["skills"] = [skill]
    for task, start, deadline in zip(data["tasks"], [40, 75], [60, 97]):
        task.update(task_type="A", required_skill=["A"], est_duration_min=20,
                    earliest_start=start, deadline=deadline)
    add("C07", "travel_after_protected_break_start77_end97", "draft", data)

    data = copy.deepcopy(base)
    data["tasks"] = data["tasks"][:1]
    data["tasks"][0].update(task_type="Z", required_skill=["Z"], deadline=20)
    data["nurses"][-1].update(skills=["Z"], available_from=40)
    add("C08", "specialist_only_available_after_deadline", "infeasible", data)

    bundle = {"data_kind": "synthetic", "seed": None,
              "generation": "deterministic modifications of P01; no random sampling",
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "assumptions": "IDs, durations, staffing, skills, coverage, windows and equipment capacities are technical test inputs; not observed hospital data or clinical thresholds.",
              "cases": cases}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"cases": len(cases), "output": str(output)}


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "data/cp3-engine-cases.json")
    args = parser.parse_args()
    print(json.dumps(build_cases(root, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
