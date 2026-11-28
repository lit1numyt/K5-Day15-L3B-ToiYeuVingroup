"""Check shared data inputs against source values and the existing planning API."""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))
from planning import draft_schedule, input_issues, validate_plan


def check_handoff(path):
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["data_kind"] == "synthetic"
    assert (
        len(bundle["cases"]) == 3
        and {c["id"] for c in bundle["cases"]} == {"P01", "P02", "P03"}
    ), "Incomplete or duplicate case IDs"
    assert set(bundle["source_sha256"]) == {
        "cp2-cases.json", "ward_task_duration.csv"
    }, "Missing source checksums"
    for name, checksum in bundle["source_sha256"].items():
        source = ROOT / ("data/" + name if name == "cp2-cases.json" else "data/reference/" + name)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == checksum, name
    with (ROOT / "data/reference/ward_task_duration.csv").open(encoding="utf-8") as stream:
        reference = {row["task_type"]: row for row in csv.DictReader(stream)}
    fixtures = json.loads((ROOT / "data/cp2-cases.json").read_text(encoding="utf-8"))
    base = next(c["input"] for c in fixtures if c["id"] == "F03")
    given = {task["task_id"]: task["est_duration_min"] for task in base["tasks"]}
    cases = {case["id"]: case for case in bundle["cases"]}
    absence = cases["P03"]["absent_nurse_id"]
    expected_absence = copy.deepcopy(cases["P02"]["instance"])
    assert absence in {n["nurse_id"] for n in expected_absence["nurses"]}, "Unknown absent nurse"
    expected_absence["nurses"] = [n for n in expected_absence["nurses"] if n["nurse_id"] != absence]
    assert cases["P03"]["instance"] == expected_absence, "Absence changes fields beyond roster"
    results = []
    for case in bundle["cases"]:
        instance = case["instance"]
        assert not input_issues(instance), case["id"]
        assert {task["task_id"] for task in instance["tasks"]} == given.keys(), "Missing source tasks"
        lookup_ids = set() if case["id"] == "P01" else set(given) - {"T1"}
        assert {
            task["task_id"] for task in instance["tasks"]
            if task["duration_source"].startswith("lookup:")
        } == lookup_ids, "Wrong given/lookup case mode"
        for patient in instance["patients"]:
            assert {
                "acuity_score", "adl_dependency", "care_category", "isolation_precaution"
            } <= patient.keys(), "Missing taxonomy inputs"
            for field in ["acuity_score", "adl_dependency"]:
                value = patient[field]
                assert type(value) in (int, float) and math.isfinite(value) and value >= 0, field
            assert isinstance(patient["care_category"], str) and patient["care_category"].strip()
            assert type(patient["isolation_precaution"]) is bool
        for nurse in instance["nurses"]:
            years = nurse.get("experience_years")
            assert (
                type(years) in (int, float) and math.isfinite(years) and years >= 0
            ), "Invalid experience_years"
        expected_l3_input = copy.deepcopy(instance)
        for task in expected_l3_input["tasks"]:
            if task["duration_source"].startswith("lookup:"):
                del task["est_duration_min"]
                del task["duration_source"]
        assert case["l3_input"] == expected_l3_input, "L3 pair changes fields beyond duration/source"
        expected = {task["task_id"]: task for task in instance["tasks"]}
        actual_missing = input_issues(case["l3_input"])
        expected_missing = []
        for task in case["l3_input"]["tasks"]:
            target = expected[task["task_id"]]
            if "est_duration_min" in task:
                assert task == target, "Given duration or other input changed"
                assert (
                    target["duration_source"] == "given"
                    and task["est_duration_min"] == given[task["task_id"]]
                ), "Given duration differs from F03"
            else:
                expected_missing.append(
                    "tasks." + task["task_id"] + ".est_duration_min: cần duration được cung cấp/xác nhận"
                )
                assert target["duration_source"] == "lookup:simmons-2025-table3"
                assert target["est_duration_min"] == math.ceil(
                    float(reference[task["task_type"]]["mean_duration_min"])
                )
        assert sorted(actual_missing) == sorted(expected_missing), actual_missing
        plan = draft_schedule(copy.deepcopy(instance))
        assert plan["status"] == "draft", case["id"]
        validation = validate_plan(instance, plan)
        assert validation["valid"], validation["violations"]
        results.append({"id": case["id"], "input_valid": True,
                        "witness_plan_valid": True,
                        "missing_duration_fields_for_l3": len(expected_missing),
                        "metrics": validation["metrics"]})
    return {"data_kind": bundle["data_kind"], "checked_cases": len(results), "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/preliminary/instances.json")
    args = parser.parse_args()
    print(json.dumps(check_handoff(args.input), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
