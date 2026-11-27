"""Workflow CP2: đọc JSON → kiểm dữ liệu → lập nháp → validate → trả kết quả.

answer(text) giữ hợp đồng harness. Khoa tích hợp điều phối LLM/CP-SAT ở CP3.
"""
import json

from ai import MODEL_PROVIDER, call_model
from tools import estimate_workload, solve_allocation, validate_plan

SYSTEM = "Bạn hỗ trợ trưởng ca; chỉ tạo bản nháp, không bỏ hard constraints hay tự duyệt."


def answer(text: str) -> dict:
    if MODEL_PROVIDER != "fake":
        raise NotImplementedError("CP2 chưa nối LLM thật; dùng MODEL_PROVIDER=fake. Tích hợp API/CP-SAT ở CP3.")
    call_model(SYSTEM, "CP2: kiểm dữ liệu, lập nháp và chờ trưởng ca duyệt.")
    try:
        instance = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        instance = None
    request = instance.get("request", {}) if isinstance(instance, dict) else {}
    if not isinstance(request, dict) or request.get("action", "plan") != "plan":
        result = {"status": "refused", "warnings": ["Không bỏ kỹ năng/coverage/task bắt buộc, không tự duyệt. CP2 chỉ nhận action=plan."]}
    else:
        issues = estimate_workload(instance)
        if issues:
            message = "Cần bổ sung dữ liệu; không suy ra task/kỹ năng từ staffing tổng hợp."
            if not isinstance(instance, dict):
                message = ("Để lập lịch đầu ca, hãy gửi một đối tượng JSON gồm shift (ca), "
                           "nurses (điều dưỡng), patients (bệnh nhân) và tasks (công việc). "
                           "Xem ví dụ nhập liệu trong README.")
            result = {"status": "need_info", "missing_fields": issues,
                      "warnings": [message]}
        else:
            result = solve_allocation(instance)
            if result["status"] == "draft":
                validation = validate_plan(instance, result)
                if validation["valid"]:
                    result["validation"] = validation
                    result["metrics"] = validation["metrics"]
                    result["explanation"] = "Đã kiểm kỹ năng, cửa giờ, tải, chuyển phòng, nghỉ và coverage theo input; trưởng ca duyệt trước khi áp dụng."
                else:
                    result = {"status": "unknown", "warnings": validation["violations"]}
    result.update(mode="cp2", approval_required=True)
    return {"output": json.dumps(result, ensure_ascii=False)}
