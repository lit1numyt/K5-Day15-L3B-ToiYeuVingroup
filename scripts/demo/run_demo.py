"""NurseFlow — demo luồng lập kế hoạch ca (CHƯA có L2 CP-SAT).

Chạy một ca mẫu qua toàn bộ pipeline hiện có và in kết quả dễ đọc:
  [L3] estimate_duration  — điền thời lượng việc còn thiếu (given / lookup Simmons)
  [Engine] answer()        — agent lập BẢN NHÁP kế hoạch (L2 = heuristic thay thế CP-SAT)
  [L4] classify_patient + baseline_allocate — taxonomy bệnh nhân + so với cách truyền thống

Model ở chế độ fake (chưa nối API) — đủ để demo luồng. Chạy từ gốc repo:
  python scripts/demo/run_demo.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from agent import answer                                  # noqa: E402  L1 (fake model)
from baseline import baseline_allocate, classify_patient  # noqa: E402  L4
from planning import validate_plan                        # noqa: E402
from workload import estimate_duration                    # noqa: E402  L3

LINE = "─" * 68


def fmt_window(start, end):
    return f"[{start:>3}–{end:<3}p]"


def main():
    bundle = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
    case = bundle["cases"][1]                       # P02: có việc thiếu thời lượng để L3 điền
    submitted = case["l3_input"]
    shift = submitted["shift"]

    print(LINE)
    print("NurseFlow · DEMO luồng lập kế hoạch ca")
    print(f"(L2 CP-SAT chưa có → dùng heuristic thay thế; model = fake)")
    print(LINE)
    print(f"Ca {shift['shift_id']} · khoa {shift['ward_id']} · {shift['shift_length_min']} phút · "
          f"{len(submitted['nurses'])} điều dưỡng · {len(submitted['patients'])} bệnh nhân · "
          f"{len(submitted['tasks'])} việc")

    # ── L3 ──────────────────────────────────────────────────────────────
    print(f"\n[L3] Ước lượng thời lượng việc")
    before = {t["task_id"]: t.get("est_duration_min") for t in submitted["tasks"]}
    instance = estimate_duration(submitted)
    for t in instance["tasks"]:
        flag = "" if before[t["task_id"]] is not None else "  ← L3 điền"
        print(f"   {t['task_id']:<3} {t['task_type']:<15} {t['est_duration_min']:>3}'"
              f"  ({t.get('duration_source')}){flag}")

    # ── L4 taxonomy ─────────────────────────────────────────────────────
    print(f"\n[L4] Phân loại bệnh nhân (taxonomy KMeans)")
    tier_name = {1: "nhẹ", 2: "trung bình", 3: "nặng"}
    for p in instance["patients"]:
        tax = classify_patient(p)
        print(f"   {p['patient_id']:<3} acuity={p['acuity_score']} adl={p['adl_dependency']}"
              f"  → tier {tax['tier']} ({tier_name.get(tax['tier'], '?')}), weight={tax['workload_weight']}")

    # ── Engine: agent lập bản nháp ──────────────────────────────────────
    print(f"\n[Engine] Kế hoạch đề xuất — BẢN NHÁP chờ trưởng ca duyệt")
    out = json.loads(answer(json.dumps(instance, ensure_ascii=False))["output"])
    if out.get("status") != "draft":
        print(f"   status={out.get('status')} · {out.get('warnings') or out.get('missing_fields')}")
        return
    types = {t["task_id"]: t["task_type"] for t in instance["tasks"]}
    by_nurse = {}
    for a in out["assignments"]:
        by_nurse.setdefault(a["nurse_id"], []).append(a)
    for nid in sorted(by_nurse):
        rows = sorted(by_nurse[nid], key=lambda a: a["start"])
        line = "  ".join(f"{a['task_id']}:{types[a['task_id']]} {fmt_window(a['start'], a['end'])}" for a in rows)
        print(f"   {nid}: {line}")
    m = out["metrics"]
    print(f"   → tải: {m['workload_minutes']} · CV={m['utilization_cv']:.3f} · "
          f"peak={m['peak_utilization']:.3f} · overhead={m['overhead_minutes']}'")
    print(f"   → {out['explanation']}")

    # ── L4 baseline comparison ──────────────────────────────────────────
    print(f"\n[L4] So với cách phân công truyền thống (cùng ca)")
    rows = [("Truyền thống — theo đầu bệnh nhân", baseline_allocate(instance, "count")),
            ("Truyền thống — acuity-weighted", baseline_allocate(instance, "weight")),
            ("NurseFlow (heuristic thay L2)", out)]
    print(f"   {'phương pháp':<36} {'CV':>7} {'peak':>7} {'overhead':>9}")
    for name, plan in rows:
        mm = plan.get("metrics") if plan.get("status") == "draft" else None
        if mm:
            print(f"   {name:<36} {mm['utilization_cv']:>7.3f} {mm['peak_utilization']:>7.3f} {mm['overhead_minutes']:>9}")
        else:
            print(f"   {name:<36} {'(' + str(plan.get('status')) + ')':>25}")

    print(f"\n{LINE}")
    print(f"Trạng thái: draft · approval_required={out.get('approval_required')} — "
          f"AI đề xuất, trưởng ca quyết định.")
    print(LINE)


if __name__ == "__main__":
    main()
