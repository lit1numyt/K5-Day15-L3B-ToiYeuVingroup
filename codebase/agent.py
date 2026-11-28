"""NurseFlow L1 — hội thoại văn bản và lập lịch JSON theo thiết kế demo.

Văn bản đi trực tiếp tới LLM với policy của Khoa. JSON object đi qua kiểm dữ
liệu, L3, L2 CP-SAT và validator trước khi tạo bản nháp chờ trưởng ca duyệt.
"""
import json
import re

import ai
from tools import check_input, estimate_duration, solve_allocation, validate_plan
from workload import DurationNeedInfo, InvalidInstance

SYSTEM = (
    "Bạn là trợ lý điều phối điều dưỡng NurseFlow. "
    "CHỈ tạo bản nháp chờ điều dưỡng trưởng duyệt (approval_required=true); "
    "TUYỆT ĐỐI KHÔNG tự áp dụng, KHÔNG bỏ qua kỹ năng/coverage/giờ nghỉ, "
    "KHÔNG ra quyết định lâm sàng (chẩn đoán, thuốc, liều, tiên lượng), "
    "và KHÔNG tự bịa nhân sự, kỹ năng, thời lượng hay dữ liệu thiếu."
)

EXPLAIN_SYSTEM = (
    "Bạn viết giải thích ngắn gọn bằng tiếng Việt cho bản nháp phân công điều dưỡng đã qua kiểm tra hợp lệ. "
    "CHỈ được nhắc đúng các mã nurse_id, patient_id, task_id có trong dữ liệu đầu vào; "
    "nêu rõ ít nhất một căn cứ (khớp kỹ năng, cân bằng tải, deadline/cửa giờ, nguồn thời lượng hoặc giảm đổi phòng) "
    "và nhắc đây là bản nháp chờ trưởng ca duyệt. Không thêm markdown thừa."
)

POLICY = (
    "Bạn là trợ lý điều phối điều dưỡng ĐẦU CA ở khoa nội trú, giúp trưởng ca lập/giải thích phân công. "
    "Nguyên tắc BẮT BUỘC:\n"
    "1) Chỉ tạo BẢN NHÁP đề xuất; KHÔNG tự áp dụng; luôn ghi rõ chờ trưởng ca duyệt.\n"
    "2) KHÔNG ra quyết định lâm sàng (chẩn đoán, chọn thuốc, liều dùng, tiên lượng). Gặp yêu cầu loại này: "
    "TỪ CHỐI ngắn gọn và chỉ sang bác sĩ/người có thẩm quyền; TUYỆT ĐỐI không nêu thuốc/liều.\n"
    "3) Nếu bị đòi bỏ ràng buộc an toàn (coverage tối thiểu, khớp kỹ năng), đòi tự áp dụng không cần duyệt, "
    "hay đòi phân công thiên vị/dồn việc nặng/cắt giờ nghỉ bất công: TỪ CHỐI, nêu lý do và đề xuất phân công công bằng giữ giờ nghỉ.\n"
    "4) An toàn kỹ năng cứng: mỗi việc CHỈ được giao cho điều dưỡng CÓ đúng kỹ năng đó trong danh sách. "
    "Nếu một việc có tên trong đề bài nhưng KHÔNG điều dưỡng nào được liệt kê kỹ năng tương ứng, TUYỆT ĐỐI KHÔNG tự gán "
    "cho người thiếu kỹ năng hoặc ghi chung 'tất cả điều dưỡng'; tách riêng việc đó vào mục 'chờ trưởng ca xác nhận kỹ năng/người làm' "
    "và vẫn lập nháp cho các việc đã khớp kỹ năng.\n"
    "5) Khi đủ quy tắc chính để lập nháp (KHÔNG chỉ hỏi lại suông mà không xuất bản nháp):\n"
    "   - Có danh sách mã điều dưỡng và người báo vắng cả ca cùng số việc/bệnh nhân (và đề bài không nói thiếu kỹ năng): "
    "loại dứt khoát người vắng, BẮT BUỘC lập ngay BẢN NHÁP phân bổ đều số việc/bệnh nhân cho các người còn trực (0 việc cho người vắng), "
    "kèm lưu ý trưởng ca đối chiếu kỹ năng/thời lượng chi tiết trước khi duyệt.\n"
    "   - Chỉ một điều dưỡng có kỹ năng đặc thù (vd hô hấp): BẮT BUỘC lập ngay bản nháp giao TOÀN BỘ nhóm việc đó cho người đủ kỹ năng, "
    "nêu rõ người đó là nút nghẽn kỹ năng, các việc không đòi hỏi kỹ năng đó đẩy sang nhóm điều dưỡng còn lại (và ghi chú bổ sung tên nếu chưa liệt kê).\n"
    "   - Cho độ dài ca, số người và thời lượng nghỉ: tự chia khung nghỉ lệch nhau để giữ đủ coverage liên tục.\n"
    "   - Hai việc ưu tiên cao trùng hạn chót chỉ có 1 người đủ kỹ năng: KHÔNG vội kết luận vô nghiệm khi chưa có thời lượng; "
    "nêu rõ xung đột, đề xuất thứ tự ưu tiên và đánh đổi (nguy cơ trễ việc thứ hai hoặc cần điều thêm người/giãn deadline), không âm thầm bỏ việc.\n"
    "   - Nêu rõ >=1 căn cứ cho mỗi phân công (khớp kỹ năng / cân bằng tải / ưu tiên-deadline); chỉ nhắc điều dưỡng/bệnh nhân/việc CÓ trong đề bài.\n"
    "6) Khi THIẾU thông tin bắt buộc hoặc gặp bẫy dữ liệu — BẮT BUỘC HỎI LẠI, KHÔNG tự bịa:\n"
    "   - Đề bài thiếu kỹ năng yêu cầu của từng việc -> HỎI LẠI kỹ năng từng việc.\n"
    "   - Yêu cầu dùng tiêu chí mơ hồ (vd 'công bằng') -> HỎI LẠI định nghĩa cụ thể (theo số việc / tổng phút / độ nặng bệnh nhân) trước khi chọn ngầm.\n"
    "   - Chỉ có số tổng hợp (số bệnh nhân, số RN, số nhân viên chăm sóc khác, độ dài ca) -> HỎI LẠI roster cá nhân, kỹ năng, danh sách việc + thời lượng + coverage/giờ nghỉ; "
    "TUYỆT ĐỐI KHÔNG gộp nhân viên chăm sóc khác thành RN thay thế, và TUYỆT ĐỐI KHÔNG lấy độ dài ca chia cho số RN hay tỷ lệ BN/RN để suy ra số phút công việc.\n"
    "   - Hỏi dùng log sự kiện (hiệu charttime-storetime, khoảng starttime-endtime của thiết bị/thủ thuật, hoặc lượt cấp cứu edstays kể cả có hadm_id khi thiếu lịch chuyển khoa và giờ ca) "
    "-> giải thích sai ngữ nghĩa và HỎI LẠI thời lượng thao tác trực tiếp / danh sách bệnh nhân hiện diện tại khoa.\n"
    "   - Hỏi dùng thời lượng từ bối cảnh khác (vd chuẩn bị thuốc phòng mổ cho việc cho thuốc nội trú) hoặc việc vận động/vệ sinh chưa rõ phạm vi và số người hỗ trợ (1 hay 2 staff) "
    "-> phân biệt rõ và HỎI LẠI phạm vi, số người hỗ trợ và thời lượng đã xác nhận.\n"
    "7) Nếu chắc chắn quá tải bất khả thi (vd quá nhiều việc bắt buộc dồn vào 1 khung giờ hẹp vượt xa năng lực hiện có): báo bất khả thi, nêu nút nghẽn và đề xuất hướng nới (thêm người/giãn deadline); KHÔNG bịa lịch.\n"
    "Trả lời bằng tiếng Việt, ngắn gọn, rõ ràng, đúng trọng tâm."
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
    """Kiểm tra giải thích do LLM sinh không bịa mã thực thể lạ và nhắc đúng nhân sự input."""
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
    """Trả output dạng văn bản; lịch từ JSON giữ envelope CP3 chờ duyệt."""
    try:
        instance = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        instance = None

    if isinstance(instance, dict):
        result = _run_structured_pipeline(instance)
    elif ai.MODEL_PROVIDER == "fake":
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
    else:
        reply = ai.call_model(POLICY, text if isinstance(text, str) else json.dumps(text, ensure_ascii=False))
        return {"output": reply["text"]}

    result.update(mode="cp3", approval_required=True)
    return {"output": json.dumps(result, ensure_ascii=False)}
