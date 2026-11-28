"""Sinh ca tổng hợp (5 điều dưỡng, 20 việc), chạy pipeline và xuất dữ liệu
cho frontend (design/wireframes/demo-data.js).

Model gọi trong luồng:
  L3 estimate_duration · L1 agent answer() (gọi call_model — THẬT nếu .env đã nối, fake nếu chưa) ·
  L4 classify_patient + baseline_allocate.
CP-SAT lập lịch, validator kiểm ràng buộc và LLM giải thích kết quả.

Chạy từ gốc repo:  python scripts/demo/build_demo.py
"""
import json
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from agent import answer                                   # noqa: E402
from ai import MODEL_PROVIDER, call_model                  # noqa: E402
from baseline import baseline_allocate, classify_patient   # noqa: E402
from planning import validate_plan                         # noqa: E402
from workload import estimate_duration                     # noqa: E402

SKILLS = ["med_admin", "vitals", "wound_care", "lab_collection", "iv_care",
          "catheter_care", "procedure_care", "hygiene"]
DUR = {"med_admin": 8, "vitals": 5, "wound_care": 12, "lab_collection": 7,
       "iv_care": 10, "catheter_care": 6, "procedure_care": 20, "hygiene": 15}
NAMES = ["An", "Bình", "Chi", "Dũng", "Em"]
OUT_JS = ROOT / "design/wireframes/demo-data.js"
OUT_JSON = ROOT / "data/demo/shift_5n_20t.json"


def build_instance():
    rng = random.Random(7)
    nurses = [{"nurse_id": f"N{i+1}", "name": NAMES[i], "skills": SKILLS[:],
               "available_from": 0, "available_to": 480, "max_capacity_min": 420,
               "home_zone": "W1", "qualification_level": 3, "experience_years": 1 + i,
               "specialization": "demo"} for i in range(5)]
    rooms = ["R1", "R2", "R3", "R4"]
    patients = [{"patient_id": f"P{i+1}", "room": rooms[i % 4], "zone": "W1",
                 "acuity_score": rng.choice([1, 2, 3, 4, 5]), "adl_dependency": rng.choice([1, 2, 3, 4]),
                 "care_category": "medical", "isolation_precaution": (i % 7 == 0)} for i in range(12)]
    types = list(DUR)
    tasks = [{"task_id": f"T{i+1}", "patient_id": patients[i % 12]["patient_id"],
              "task_type": types[i % len(types)], "required_skill": [types[i % len(types)]],
              "est_duration_min": DUR[types[i % len(types)]], "duration_source": "given",
              "earliest_start": 0, "deadline": 480, "mandatory": True,
              "required_skill_level": 1, "priority": rng.choice([1, 2, 3]), "frequency": "once"}
             for i in range(20)]
    shift = {"shift_id": "S1", "ward_id": "W1", "shift_length_min": 480, "room_switch_min": 2,
             "break_policy": {"duration_min": 30, "window": [120, 300]},
             "coverage_rules": [{"start": 0, "end": 480, "zone": "W1", "required_skill": None, "min_staff": 2}],
             "census": 12}
    return {"shift": shift, "nurses": nurses, "patients": patients, "tasks": tasks,
            "request": {"action": "plan"}}


def main():
    instance = build_instance()

    # L3 — điền/giữ thời lượng
    instance = estimate_duration(instance)

    # L1 — agent lập bản nháp (gọi call_model thật nếu .env đã nối)
    out = json.loads(answer(json.dumps(instance, ensure_ascii=False))["output"])
    if out.get("status") != "draft":
        sys.exit(f"Engine không ra draft: {out.get('status')} · {out.get('warnings') or out.get('missing_fields')}")
    validation = validate_plan(instance, out)
    if not validation["valid"] or out.get("method") != "cp_sat":
        sys.exit(f"Cần lịch CP-SAT qua validator: {validation['violations']}")

    # AI tóm tắt kế hoạch (một lời gọi model thật nữa, gắn với chính kế hoạch này)
    names = {n["nurse_id"]: n.get("name", n["nurse_id"]) for n in instance["nurses"]}
    per = {}
    for a in out["assignments"]:
        per.setdefault(a["nurse_id"], []).append(a["task_id"])
    plan_desc = "; ".join(f"{names[n]}: {len(v)} việc" for n, v in sorted(per.items()))
    ai = call_model(
        "Bạn là trợ lý điều phối điều dưỡng. Chỉ tóm tắt kế hoạch cho điều dưỡng trưởng bằng tiếng Việt, "
        "ngắn gọn, nêu căn cứ (cân bằng tải/kỹ năng), KHÔNG ra quyết định lâm sàng, KHÔNG tự áp dụng.",
        f"Ca S1, 5 điều dưỡng, 20 việc. Phân bổ: {plan_desc}. "
        f"Chỉ số: CV={out['metrics']['utilization_cv']:.3f}, peak={out['metrics']['peak_utilization']:.3f}. "
        "Tóm tắt 2-3 câu cho điều dưỡng trưởng.")

    # L4 — taxonomy + baseline đối chứng
    taxonomy = {p["patient_id"]: classify_patient(p) for p in instance["patients"]}
    base_count = baseline_allocate(instance, "count")
    base_weight = baseline_allocate(instance, "weight")

    def metrics_of(plan):
        return plan.get("metrics") if plan.get("status") == "draft" else None

    demo = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "data_kind": "synthetic", "seed": 7, "display_start_min": 420,
        "model": {"provider": MODEL_PROVIDER, "name": ai.get("model"),
                  "tokens_in": ai.get("tokens_in"), "tokens_out": ai.get("tokens_out")},
        "shift": instance["shift"],
        "nurses": [{"nurse_id": n["nurse_id"], "name": n.get("name")} for n in instance["nurses"]],
        "patients": instance["patients"],
        "tasks": instance["tasks"],
        "plan": {"status": out["status"], "approval_required": out["approval_required"],
                 "method": out["method"], "validation": validation,
                 "unassigned_tasks": out["unassigned_tasks"],
                 "assignments": out["assignments"], "breaks": out["breaks"],
                 "metrics": out["metrics"], "explanation": out["explanation"]},
        "taxonomy": taxonomy,
        "ai_text": ai["text"],
        "baselines": {"count": metrics_of(base_count), "weight": metrics_of(base_weight),
                      "nurseflow": out["metrics"]},
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(instance, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_JS.write_text("window.NURSEFLOW_DEMO = "
                      + json.dumps(demo, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")

    print(f"model={MODEL_PROVIDER} ({ai.get('model')}) · token in/out={ai.get('tokens_in')}/{ai.get('tokens_out')}")
    print(f"plan: {len(out['assignments'])} việc / {len(instance['nurses'])} điều dưỡng · CV={out['metrics']['utilization_cv']:.3f}")
    print(f"wrote {OUT_JS.relative_to(ROOT)} và {OUT_JSON.relative_to(ROOT)}")
    if MODEL_PROVIDER == "fake":
        print("⚠ model=fake (chưa nối API). Nối model thật: tạo .env (xem .env.example) rồi chạy lại.")


if __name__ == "__main__":
    main()
