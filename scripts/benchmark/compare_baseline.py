"""Compare Khoa's count/acuity-weighted L4, Lam's CP-SAT and the CP2 heuristic.

Every draft is independently revalidated on the same original instance. This
technical comparison is separate from the hackathon's conversational benchmark.
"""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from baseline import baseline_allocate
from cp_sat_engine import solve_allocation, RANDOM_SEED, TIME_LIMIT_SECONDS
from planning import draft_schedule, validate_plan
import ortools


def evaluate_plan(instance, plan):
    """Use only the shared oracle's metrics; invalid drafts are never scored."""
    status = plan.get("status", "unknown")
    result = {"status": status, "valid": None, "violations": [], "metrics": None}
    if status == "draft":
        checked = validate_plan(instance, plan)
        result.update(valid=checked["valid"], violations=checked["violations"])
        if checked["valid"]:
            result["metrics"] = checked["metrics"]
    return result


def compare_cases(cases, allocators):
    records = []
    for case in cases:
        original = copy.deepcopy(case["instance"])
        checksum = hashlib.sha256(json.dumps(
            original, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        for name, allocate in allocators.items():
            start = time.perf_counter()
            plan = allocate(copy.deepcopy(original))
            elapsed = (time.perf_counter() - start) * 1000
            records.append({"case_id": case["id"], "allocator": name,
                            "input_sha256": checksum, "input": copy.deepcopy(original),
                            "output": plan, "elapsed_ms": round(elapsed, 3),
                            **evaluate_plan(original, plan)})
    return records


def save_comparison(records, output_dir, metadata):
    """Allocate a fresh run name, preserving both old JSON and old CSV outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    number = 1
    while any((output_dir / f"l2-comparison-{number}{suffix}").exists() for suffix in (".json", ".csv")):
        number += 1
    output = output_dir / f"l2-comparison-{number}.json"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"metadata": metadata, "records": records}, ensure_ascii=False, indent=2) + "\n")
    fields = ["case_id", "allocator", "status", "valid", "input_sha256", "elapsed_ms",
              "utilization_cv", "peak_utilization", "overhead_minutes", "violations"]
    with output.with_suffix(".csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for record in records:
            row = {key: record[key] for key in fields[:6]}
            metrics = record["metrics"] or {}
            row.update({key: metrics.get(key) for key in fields[6:9]})
            row["violations"] = " | ".join(record["violations"])
            writer.writerow(row)
    return output


def metadata():
    paths = ["codebase/cp_sat_engine.py", "codebase/planning.py", "codebase/baseline.py",
             "codebase/L4/taxonomy_meta.json", "scripts/benchmark/compare_baseline.py",
             "data/preliminary/instances.json", "data/cp3-engine-cases.json", "requirements.txt"]
    try:
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    return {"purpose": "synthetic technical allocation comparison; not conversational AI evaluation",
            "git_revision": revision, "python": platform.python_version(), "ortools": ortools.__version__,
            "seed": RANDOM_SEED, "time_limit_s": TIME_LIMIT_SECONDS, "workers": 1,
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
            "baseline_policy": "patient_count and acuity_weight; one nurse per patient; stricter than task allocation",
            "clinical_validation": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval")
    args = parser.parse_args()
    cases = []
    for relative in ["data/preliminary/instances.json", "data/cp3-engine-cases.json"]:
        cases.extend(json.loads((ROOT / relative).read_text(encoding="utf-8"))["cases"])
    records = compare_cases(cases, {"l4_patient_count": baseline_allocate,
                                    "l4_patient_weight": lambda instance: baseline_allocate(instance, "weight"),
                                    "cp_sat": solve_allocation, "cp2_heuristic": draft_schedule})
    print(f"{'case':5s} {'method':18s} {'status':11s} {'valid':5s} {'CV':>7s} {'peak':>7s} {'travel':>7s} {'ms':>9s}")
    for record in records:
        metrics = record["metrics"]
        values = (f"{metrics['utilization_cv']:7.3f} {metrics['peak_utilization']:7.3f} "
                  f"{metrics['overhead_minutes']:7d}" if metrics else f"{'-':>7s} {'-':>7s} {'-':>7s}")
        print(f"{record['case_id']:5s} {record['allocator']:18s} {record['status']:11s} "
              f"{str(record['valid']):5s} {values} {record['elapsed_ms']:9.3f}")
    path = save_comparison(records, args.output_dir, metadata())
    print("Saved:", path)


if __name__ == "__main__":
    main()
