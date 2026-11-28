"""Workflow CP3 (Giai đoạn 2): parse -> check cấu trúc -> L3 estimate_duration -> L2 -> validate_plan -> explain.

answer(text) giữ hợp đồng harness: trả về {"output": <json string>} với mode="cp3", approval_required=True.
"""
import json
import re

import ai
from tools import check_input, estimate_duration, solve_allocation, validate_plan
from workload import DurationNeedInfo, InvalidInstance

SYSTEM = (
    "Bạn hỗ trợ điều dưỡng trưởng ca lập bản nháp phân công. "
    "Chỉ tạo bản nháp chờ người duyệt, không bỏ ràng buộc kỹ năng/coverage, "
    "không bịa nhân sự/thời lượng, không tự áp dụng hay ra quyết định lâm sàng."
)

EXPLAIN_SYSTEM = (
    "Bạn viết giải thích ngắn gọn bằng tiếng Việt cho bản nháp phân công điều dưỡng đã qua kiểm tra hợp lệ. "
    "CHỈ được nhắc đúng các mã nurse_id, patient_id, task_id có trong dữ liệu đầu vào; "
    "nêu rõ ít nhất một căn cứ (khớp kỹ năng, cân bằng tải, deadline/cửa giờ, nguồn thời lượng hoặc giảm đổi phòng) "
    "và nhắc đây là bản nháp chờ trưởng ca duyệt. Không thêm markdown thừa."
)

_ID_TOKEN_RE = re.compile(r"\b(?:N|P|T|R|W|S)\d+\b")


def _build_grounded_explanation(instance: dict, plan: dict, metrics: dict) -> str:
    """Tạo giải thích có căn cứ 100% từ dữ liệu đã validate (dùng cho fallback hoặc chế độ fake)."""
    tasks_by_id = {t["task_id"]: t for t in instance["tasks"]}
    assignments = plan.get("assignments", [])
    loads = metrics.get("workload_minutes", {})
    sources = sorted({t.get("duration_source", "given") for t in instance["tasks"]})
    sample_parts = []
    for row in assignments[:4]:
        task = tasks_by_id.get(row["task_id"], {})
        skills = ",".join(task.get("required_skill", []))
        sample_parts.append(
            f"{row['task_id']} ({row['nurse_id']}→{task.get('patient_id', '?')}, "
            f"kỹ năng [{skills}], {row['start']}–{row['end']}p)"
        )
    if len(assignments) > 4:
        sample_parts.append(f"... tổng {len(assignments)} task")
    load_str = ", ".join(f"{nid}={mins}p" for nid, mins in loads.items())
    cv = metrics.get("utilization_cv", 0.0)
    overhead = metrics.get("overhead_minutes", 0)
    return (
        f"Bản nháp đã qua validator (chờ trưởng ca duyệt): {'; '.join(sample_parts)}. "
        f"Tải từng điều dưỡng: {load_str} (CV={cv:.4f}, đổi phòng={overhead}p; "
        f"nguồn thời lượng: {', '.join(sources)})."
    )


def _valid_llm_explanation(text: str, instance: dict) -> bool:
    """Kiểm tra giải thích do LLM sinh không bịa mã thực thể lạ và nhắc đúng yếu tố duyệt."""
    cleaned = (text or "").strip()
    if len(cleaned) < 20:
        return False
    known_ids = (
        {instance["shift"]["shift_id"], instance["shift"]["ward_id"]}
        | {n["nurse_id"] for n in instance["nurses"]}
        | {p["patient_id"] for p in instance["patients"]}
        | {p["room"] for p in instance["patients"]}
        | {t["task_id"] for t in instance["tasks"]}
    )
    mentioned_ids = set(_ID_TOKEN_RE.findall(cleaned))
    if not mentioned_ids.issubset(known_ids):
        return False
    return any(n["nurse_id"] in cleaned for n in instance["nurses"])


def _explain_draft(instance: dict, plan: dict, metrics: dict) -> str:
    """Sinh giải thích có căn cứ cho bản nháp hợp lệ."""
    fallback = _build_grounded_explanation(instance, plan, metrics)
    if ai.MODEL_PROVIDER == "fake":
        ai.call_model(SYSTEM, "CP3: kiểm dữ liệu, ước lượng L3, lập nháp và chờ trưởng ca duyệt.")
        return fallback
    prompt_payload = {
        "shift_id": instance["shift"]["shift_id"],
        "nurses": [{"nurse_id": n["nurse_id"], "skills": n["skills"]} for n in instance["nurses"]],
        "tasks": [
            {
                "task_id": t["task_id"],
                "patient_id": t["patient_id"],
                "task_type": t["task_type"],
                "required_skill": t["required_skill"],
                "est_duration_min": t["est_duration_min"],
                "duration_source": t.get("duration_source"),
                "deadline": t["deadline"],
            }
            for t in instance["tasks"]
        ],
        "assignments": plan.get("assignments", []),
        "breaks": plan.get("breaks", []),
        "metrics": metrics,
    }
    res = ai.call_model(EXPLAIN_SYSTEM, json.dumps(prompt_payload, ensure_ascii=False))
    candidate = (res.get("text") or "").strip()
    return candidate if _valid_llm_explanation(candidate, instance) else fallback


def _run_structured_pipeline(instance: dict) -> dict:
    """Luồng chuẩn cho JSON ca trực: check request -> check cấu trúc -> L3 -> check đủ -> L2 -> validate."""
    request = instance.get("request", {})
    if not isinstance(request, dict) or request.get("action", "plan") != "plan":
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Từ chối yêu cầu ngoài quyền/bỏ ràng buộc.")
        return {
            "status": "refused",
            "warnings": [
                "Không bỏ kỹ năng/coverage/task bắt buộc, không tự áp dụng. "
                "Hệ thống chỉ tạo bản nháp (action=plan) chờ trưởng ca duyệt."
            ],
        }

    structural_issues = check_input(instance, require_duration=False)
    if structural_issues:
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Yêu cầu bổ sung cấu trúc đầu vào.")
        return {
            "status": "need_info",
            "missing_fields": structural_issues,
            "warnings": ["Cần bổ sung dữ liệu cấu trúc; không tự suy ra task hay kỹ năng."],
        }

    try:
        estimated_instance = estimate_duration(instance)
    except InvalidInstance as exc:
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Yêu cầu sửa cấu trúc đầu vào L3.")
        return {
            "status": "need_info",
            "missing_fields": list(exc.issues),
            "warnings": ["Dữ liệu đầu vào chưa đúng cấu trúc để ước lượng thời lượng."],
        }
    except DurationNeedInfo as exc:
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Hỏi bổ sung thời lượng hoặc điều kiện công việc.")
        return {
            "status": "need_info",
            "missing_fields": list(exc.missing_fields),
            "warnings": ["Cần bổ sung thời lượng đã xác nhận hoặc điều kiện công việc trước khi lập lịch."],
        }

    full_issues = check_input(estimated_instance, require_duration=True)
    if full_issues:
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Yêu cầu bổ sung dữ liệu sau ước lượng L3.")
        return {
            "status": "need_info",
            "missing_fields": full_issues,
            "warnings": ["Cần bổ sung dữ liệu còn thiếu trước khi lập lịch."],
        }

    plan = solve_allocation(estimated_instance)
    if plan["status"] != "draft":
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, f"Trả trạng thái {plan['status']} từ solver.")
        return plan

    validation = validate_plan(estimated_instance, plan)
    if not validation["valid"]:
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Validator bác kế hoạch.")
        return {"status": "unknown", "warnings": validation["violations"]}

    plan["validation"] = validation
    plan["metrics"] = validation["metrics"]
    plan["explanation"] = _explain_draft(estimated_instance, plan, validation["metrics"])
    return plan


def answer(text: str) -> dict:
    """Điểm vào chính của L1 cho harness và CLI."""
    try:
        instance = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        instance = None

    if isinstance(instance, dict):
        result = _run_structured_pipeline(instance)
    else:
        if ai.MODEL_PROVIDER == "fake":
            ai.call_model(SYSTEM, "Đầu vào chưa có cấu trúc JSON.")
        result = {
            "status": "need_info",
            "missing_fields": ["input: cần JSON object hoặc mô tả đủ shift, nurses, patients, tasks"],
            "warnings": [
                "Để lập lịch đầu ca, hãy gửi một đối tượng JSON gồm shift (ca), "
                "nurses (điều dưỡng), patients (bệnh nhân) và tasks (công việc). "
                "Xem ví dụ nhập liệu trong README."
            ],
        }

    result.update(mode="cp3", approval_required=True)
    return {"output": json.dumps(result, ensure_ascii=False)}
