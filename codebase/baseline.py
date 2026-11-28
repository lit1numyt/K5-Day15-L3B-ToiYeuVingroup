"""L4 · Taxonomy bệnh nhân + baseline phân công truyền thống (Khoa).

Hai hàm theo module contract §3.4:

- `classify_patient(patient)` — ánh xạ thuộc tính bệnh nhân → bậc (tier) + trọng số
  workload TƯƠNG ĐỐI, theo tinh thần thang McGill (ordinal 1–3 mỗi chiều, cộng dồn).
  KHÔNG quy ra phút: chưa có phép đổi điểm→phút được xác minh (xem eda-report §3,
  data/reference/mcgill_workload_items.csv). Trọng số chờ hiệu chỉnh bằng dữ liệu
  task–patient liên kết; hiện chỉ dùng để xếp hạng/so sánh, không nạp trực tiếp làm
  thời lượng cho solver.

- `baseline_allocate(instance)` — cách phân công TRUYỀN THỐNG theo đầu bệnh nhân
  (continuity of care: mọi task của một bệnh nhân giao cùng một điều dưỡng; cân bằng
  theo SỐ bệnh nhân, KHÔNG tối ưu cân bằng tải / gom việc). Trả `plan` đi qua đúng
  `validate_plan` để benchmark đối đầu với L2 (CP-SAT) trên cùng instance. Chỉ tạo bản
  nháp, không tự áp dụng.
"""
from planning import draft_schedule, input_issues, overlap, validate_plan  # noqa: F401

# Thang giả định của fixture kỹ thuật: acuity 1–5, adl 1–4, isolation +1.
# Cắt bậc tương đối; không phải phút, không phải điểm McGill tuyệt đối.
_TIER_CUTS = ((3, 1), (6, 2))  # weight<=3 -> tier1; <=6 -> tier2; else tier3


def classify_patient(patient):
    """patient dict -> {tier, workload_weight, care_category, basis} hoặc need_info."""
    acuity = patient.get("acuity_score")
    adl = patient.get("adl_dependency")
    if not (type(acuity) is int and type(adl) is int and acuity >= 1 and adl >= 1):
        return {"tier": None, "workload_weight": None,
                "care_category": patient.get("care_category"),
                "need_info": ["acuity_score", "adl_dependency"],
                "basis": "Thiếu acuity/adl hợp lệ; không suy đoán bậc workload."}
    weight = acuity + adl + (1 if patient.get("isolation_precaution") else 0)
    tier = 3
    for cut, value in _TIER_CUTS:
        if weight <= cut:
            tier = value
            break
    return {"tier": tier, "workload_weight": weight,
            "care_category": patient.get("care_category"),
            "basis": "McGill ordinal (acuity+adl+isolation) — trọng số tương đối, không phải phút."}


def _staggered_breaks(shift, nurses):
    """Nghỉ luân phiên trong cửa nghỉ để giữ coverage (giống heuristic L2)."""
    policy = shift["break_policy"]
    rests = [{"nurse_id": n["nurse_id"],
              "start": policy["window"][0] + i * policy["duration_min"],
              "end": policy["window"][0] + (i + 1) * policy["duration_min"]}
             for i, n in enumerate(nurses)]
    if any(b["end"] > policy["window"][1] for b in rests):
        return None
    return rests


def baseline_allocate(instance):
    """Phân công theo đầu bệnh nhân, trả plan (draft/need_info/infeasible/unknown)."""
    issues = input_issues(instance)
    if issues:
        return {"status": "need_info", "approval_required": True,
                "missing_fields": issues, "method": "baseline_patient_count",
                "warnings": ["Baseline cần input hợp lệ như L2; không tự suy dữ liệu thiếu."]}

    shift, nurses = instance["shift"], instance["nurses"]
    patients = {p["patient_id"]: p for p in instance["patients"]}
    tasks = instance["tasks"]
    rests = _staggered_breaks(shift, nurses)
    if rests is None:
        return {"status": "unknown", "approval_required": True,
                "method": "baseline_patient_count",
                "warnings": ["Baseline chưa bố trí được nghỉ luân phiên trong cửa nghỉ; cần review."]}
    rest_by_nurse = {b["nurse_id"]: b for b in rests}

    by_patient = {}
    for task in tasks:
        by_patient.setdefault(task["patient_id"], []).append(task)

    # Gán trọn mỗi bệnh nhân cho một điều dưỡng đủ skill/level/zone; cân bằng SỐ bệnh nhân.
    counts = {n["nurse_id"]: 0 for n in nurses}
    patient_nurse = {}
    for pid in sorted(by_patient, key=lambda x: (patients[x]["zone"], patients[x]["room"], x)):
        zone = patients[pid]["zone"]
        pt_tasks = by_patient[pid]
        eligible = [n for n in nurses if n["home_zone"] == zone and all(
            set(t["required_skill"]).issubset(n["skills"])
            and ("required_skill_level" not in t
                 or n.get("qualification_level", 0) >= t["required_skill_level"])
            for t in pt_tasks)]
        if not eligible:
            return {"status": "infeasible", "approval_required": True,
                    "method": "baseline_patient_count",
                    "warnings": [pid + ": không điều dưỡng nào đủ skill/level/zone cho mọi task "
                                 "của bệnh nhân (baseline giữ continuity of care)."]}
        chosen = min(eligible, key=lambda n: (counts[n["nurse_id"]], n["nurse_id"]))
        patient_nurse[pid] = chosen["nurse_id"]
        counts[chosen["nurse_id"]] += 1

    # Xếp giờ cho từng điều dưỡng: việc sớm trước, tránh break, cộng travel khi đổi phòng.
    assignments = []
    for nurse in nurses:
        nid = nurse["nurse_id"]
        rest = rest_by_nurse[nid]
        mine = sorted((t for t in tasks if patient_nurse[t["patient_id"]] == nid),
                      key=lambda t: (t["earliest_start"], t["deadline"],
                                     patients[t["patient_id"]]["room"], t["task_id"]))
        cursor, last_room, load = nurse["available_from"], None, 0
        for task in mine:
            room = patients[task["patient_id"]]["room"]
            travel = shift["room_switch_min"] if last_room is not None and last_room != room else 0
            duration = task["est_duration_min"]
            low = max(task["earliest_start"], cursor + travel, nurse["available_from"])
            high = min(task["deadline"], nurse["available_to"]) - duration
            placed = None
            start = low
            while start <= high:
                if overlap((start - travel, start + duration), (rest["start"], rest["end"])):
                    start = rest["end"] + travel  # nhảy qua giờ nghỉ
                    continue
                placed = (start, start + duration)
                break
            if placed is None:
                return {"status": "unknown", "approval_required": True,
                        "method": "baseline_patient_count",
                        "warnings": [task["task_id"] + ": baseline không xếp được trong cửa giờ/nghỉ; "
                                     "không kết luận infeasible."]}
            start, end = placed
            assignments.append({"task_id": task["task_id"], "nurse_id": nid,
                                "start": start, "end": end})
            load += travel + duration
            cursor, last_room = end, room
            if load > nurse["max_capacity_min"]:
                return {"status": "unknown", "approval_required": True,
                        "method": "baseline_patient_count",
                        "warnings": [nid + ": chia theo đầu bệnh nhân vượt capacity; cần thêm người "
                                     "(hạn chế vốn có của cách phân truyền thống)."]}

    plan = {"status": "draft", "approval_required": True, "assignments": assignments,
            "breaks": rests, "unassigned_tasks": [], "warnings": [],
            "method": "baseline_patient_count"}
    validation = validate_plan(instance, plan)
    if not validation["valid"]:
        return {"status": "unknown", "approval_required": True,
                "method": "baseline_patient_count", "warnings": validation["violations"]}
    plan["validation"] = validation
    plan["metrics"] = validation["metrics"]
    plan["explanation"] = ("Baseline truyền thống: mỗi bệnh nhân giao trọn cho một điều dưỡng, "
                           "cân bằng theo SỐ bệnh nhân (không xét acuity/tải). Bản nháp chờ trưởng ca duyệt.")
    return plan
