"""So sánh L4 baseline (phân theo đầu bệnh nhân) với L2 trên cùng instance.

L2 hiện dùng heuristic CP2 (`planning.draft_schedule`) làm STAND-IN; thay bằng CP-SAT
của Lam khi xong (cùng `plan` schema, cùng `validate_plan`). Chỉ số cho nhánh pitch
(benchmark nghiên cứu), KHÔNG phải metric hackathon.

Chạy từ gốc repo:  python scripts/benchmark/compare_baseline.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from baseline import baseline_allocate, classify_patient  # noqa: E402
from planning import draft_schedule, validate_plan  # noqa: E402


def _metrics(instance, plan):
    if plan.get("status") != "draft":
        return plan.get("status", "?"), None
    metrics = plan.get("metrics") or validate_plan(instance, plan).get("metrics", {})
    return "draft", metrics


def _fmt(status, metrics):
    if metrics is None:
        return f"{status:9s} {'-':>7s} {'-':>7s} {'-':>9s}"
    return (f"{status:9s} {metrics['utilization_cv']:7.3f} "
            f"{metrics['peak_utilization']:7.3f} {metrics['overhead_minutes']:9d}")


def main():
    bundle = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
    for case in bundle["cases"]:
        instance, cid = case["instance"], case["id"]
        print(f"\n=== {cid} — {case.get('purpose', '')} ===")
        print("  Taxonomy bệnh nhân (L4):")
        for patient in instance["patients"]:
            tax = classify_patient(patient)
            print(f"    {patient['patient_id']}: tier={tax['tier']} "
                  f"weight={tax['workload_weight']} ({tax['care_category']})")

        base_status, base_metrics = _metrics(instance, baseline_allocate(instance))
        l2_status, l2_metrics = _metrics(instance, draft_schedule(instance))

        print(f"\n  {'method':34s} {'status':9s} {'CV':>7s} {'peak':>7s} {'overhead':>9s}")
        print(f"  {'L4 baseline (đầu bệnh nhân)':34s} {_fmt(base_status, base_metrics)}")
        print(f"  {'L2 stand-in (heuristic CP2)':34s} {_fmt(l2_status, l2_metrics)}")
        if base_metrics and l2_metrics:
            dcv = base_metrics["utilization_cv"] - l2_metrics["utilization_cv"]
            print(f"  → chênh CV (baseline − L2): {dcv:+.3f}  "
                  f"(CV thấp hơn = tải cân bằng hơn)")

    print("\nGhi chú: 'L2 stand-in' là heuristic CP2, thay bằng CP-SAT của Lam khi tích hợp.")


if __name__ == "__main__":
    main()
