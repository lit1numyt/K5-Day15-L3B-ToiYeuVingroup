"""Sinh ca tổng hợp (5 điều dưỡng, 20 bệnh nhân, 44 việc), chạy pipeline và xuất dữ liệu
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
import unicodedata
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
DUR = {"med_admin": 20, "vitals": 15, "wound_care": 30, "lab_collection": 18,
       "iv_care": 25, "catheter_care": 20, "procedure_care": 45, "hygiene": 35}
# Tên đầy đủ cho 5 điều dưỡng (N1–N5) + trưởng ca. Username = tên gọi + chữ cái đầu phần còn lại.
NURSE_NAMES = ["Nguyễn Thị An", "Trần Văn Bình", "Lê Thị Cúc", "Phạm Minh Dũng", "Hoàng Thị Hoa"]
MANAGER_NAME = "Đông Hữu Nguyễn Khoa"
PASSWORD = "vinai_hackathon"
N_PATIENTS = 20
N_TASKS = 44
OUT_JS = ROOT / "design/wireframes/demo-data.js"
OUT_ACCOUNTS = ROOT / "design/wireframes/accounts.js"
OUT_JSON = ROOT / "data/demo/shift_5n_20t.json"


def _no_diacritics(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")


def username(fullname):
    """given name (từ cuối) + chữ cái đầu các phần còn lại, bỏ dấu, viết thường."""
    parts = fullname.split()
    base = parts[-1] + "".join(p[0] for p in parts[:-1])
    return _no_diacritics(base).lower()


def build_accounts():
    accounts = [{"username": username(NURSE_NAMES[i]), "password": PASSWORD, "role": "nurse",
                 "nurse_id": f"N{i+1}", "name": NURSE_NAMES[i]} for i in range(5)]
    accounts.append({"username": username(MANAGER_NAME), "password": PASSWORD, "role": "lead",
                     "nurse_id": None, "name": MANAGER_NAME})
    return accounts


def build_instance():
    rng = random.Random(7)
    nurses = [{"nurse_id": f"N{i+1}", "name": NURSE_NAMES[i], "skills": SKILLS[:],
               "available_from": 0, "available_to": 480, "max_capacity_min": 420,
               "home_zone": "W1", "qualification_level": 3, "experience_years": 1 + i,
               "specialization": "demo"} for i in range(5)]
    rooms = ["R1", "R2", "R3", "R4"]
    patients = [{"patient_id": f"P{i+1}", "room": rooms[i % 4], "zone": "W1",
                 "acuity_score": rng.choice([1, 2, 3, 4, 5]), "adl_dependency": rng.choice([1, 2, 3, 4]),
                 "care_category": "medical", "isolation_precaution": (i % 7 == 0)} for i in range(N_PATIENTS)]
    types = list(DUR)
    band = 120                    # chia ca 480' thành 4 khung 120' để việc trải đều toàn ca
    n_bands = 480 // band
    tasks = []
    for i in range(N_TASKS):
        task_type = types[i % len(types)]
        start = (i % n_bands) * band   # xoay vòng khung giờ → việc rải khắp ca, không dồn đầu ca
        tasks.append({"task_id": f"T{i+1}", "patient_id": patients[i % N_PATIENTS]["patient_id"],
                      "task_type": task_type, "required_skill": [task_type],
                      "est_duration_min": DUR[task_type], "duration_source": "given",
                      "earliest_start": start, "deadline": start + band, "mandatory": True,
                      "required_skill_level": 1, "priority": rng.choice([1, 2, 3]), "frequency": "once"})
    shift = {"shift_id": "S1", "ward_id": "W1", "shift_length_min": 480, "room_switch_min": 2,
             "break_policy": {"duration_min": 30, "window": [120, 300]},
             "coverage_rules": [{"start": 0, "end": 480, "zone": "W1", "required_skill": None, "min_staff": 2}],
             "census": N_PATIENTS}
    return {"shift": shift, "nurses": nurses, "patients": patients, "tasks": tasks,
            "request": {"action": "plan"}}


def summarize_plan(plan):
    """Tóm tắt từ số liệu của bản nháp đã được kiểm."""
    minutes = plan["metrics"]["workload_minutes"].values()
    return call_model(
        "Tóm tắt cho trưởng ca bằng tiếng Việt trong tối đa hai câu. "
        "Nêu số việc, số lượt nghỉ và khoảng thời lượng dự kiến mỗi điều dưỡng. "
        "Chỉ dùng số liệu đã cho. Nhắc đây là bản nháp chờ trưởng ca duyệt.",
        f"Đã xếp {len(plan['assignments'])} công việc và {len(plan['breaks'])} lượt nghỉ. "
        f"Tổng phút công việc dự kiến của mỗi điều dưỡng nằm trong khoảng "
        f"{min(minutes)}–{max(minutes)} phút. Bản nháp đã qua kiểm ràng buộc."
    )


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

    ai = summarize_plan(out)

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

    accounts = build_accounts()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(instance, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_JS.write_text("window.NURSEFLOW_DEMO = "
                      + json.dumps(demo, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    OUT_ACCOUNTS.write_text("window.NURSEFLOW_ACCOUNTS = "
                            + json.dumps(accounts, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")

    print(f"model={MODEL_PROVIDER} ({ai.get('model')}) · token in/out={ai.get('tokens_in')}/{ai.get('tokens_out')}")
    print(f"plan: {len(out['assignments'])} việc / {len(instance['nurses'])} điều dưỡng · "
          f"{len(instance['patients'])} bệnh nhân · CV={out['metrics']['utilization_cv']:.3f}")
    print(f"accounts: {', '.join(a['username'] for a in accounts)}")
    print(f"wrote {OUT_JS.relative_to(ROOT)}, {OUT_ACCOUNTS.relative_to(ROOT)}, {OUT_JSON.relative_to(ROOT)}")
    if MODEL_PROVIDER == "fake":
        print("⚠ model=fake (chưa nối API). Nối model thật: tạo .env (xem .env.example) rồi chạy lại.")


if __name__ == "__main__":
    main()
