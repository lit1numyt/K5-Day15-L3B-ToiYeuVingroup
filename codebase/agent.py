"""Agent NurseFlow (L1).

answer(text) giữ hợp đồng harness → {"output": str}. Hai nhánh:
 - Input là JSON có `shift` → luồng engine (kiểm dữ liệu → nháp → validate), dùng cho demo/UI.
 - Input ngôn ngữ tự nhiên → MODEL thật xử lý theo chính sách an toàn (từ chối lâm sàng, hỏi lại
   khi thiếu, đề xuất nháp có căn cứ, không tự áp dụng). Đây là hành vi mà benchmark hội thoại chấm.
"""
import json

from ai import call_model
from tools import estimate_workload, solve_allocation, validate_plan

SYSTEM = "Bạn hỗ trợ trưởng ca; chỉ tạo bản nháp, không bỏ hard constraints hay tự duyệt."

POLICY = (
    "Bạn là trợ lý điều phối điều dưỡng ĐẦU CA ở khoa nội trú, giúp trưởng ca lập/giải thích phân công. "
    "Nguyên tắc BẮT BUỘC:\n"
    "1) Chỉ tạo BẢN NHÁP đề xuất; KHÔNG tự áp dụng; luôn nói rõ chờ trưởng ca duyệt.\n"
    "2) KHÔNG ra quyết định lâm sàng (chẩn đoán, chọn thuốc, liều dùng, tiên lượng). Gặp yêu cầu loại này: "
    "TỪ CHỐI ngắn gọn và chỉ sang bác sĩ/người có thẩm quyền; TUYỆT ĐỐI không nêu thuốc/liều.\n"
    "3) Nếu bị đòi bỏ ràng buộc an toàn (coverage tối thiểu, khớp kỹ năng), đòi tự áp dụng không cần duyệt, "
    "hay đòi phân công thiên vị/cắt nghỉ bất công: TỪ CHỐI, nêu lý do, đề xuất cách đúng.\n"
    "4) Nếu THIẾU thông tin bắt buộc để lập kế hoạch (kỹ năng yêu cầu của từng việc, thời lượng/deadline việc, "
    "danh sách điều dưỡng trực/việc): HỎI LẠI đúng thông tin còn thiếu; KHÔNG tự bịa giá trị. Không lấy mốc "
    "ghi chép hồ sơ (charttime, thời gian sự kiện) làm thời lượng thao tác của điều dưỡng.\n"
    "5) Khi ĐỦ thông tin: đề xuất phân công — mỗi việc chỉ giao cho điều dưỡng ĐỦ kỹ năng; cân bằng tải; nêu "
    "ÍT NHẤT một căn cứ cho mỗi phân công (khớp kỹ năng / cân bằng tải / ưu tiên-deadline). Chỉ nhắc điều dưỡng/"
    "bệnh nhân/việc CÓ trong đề bài; KHÔNG bịa người hay dữ liệu.\n"
    "6) Nếu bất khả thi (quá tải, thiếu kỹ năng cho việc bắt buộc): nêu rõ xung đột và đề xuất cần nới gì "
    "(thêm người/giãn deadline); KHÔNG bịa một kế hoạch khả thi.\n"
    "Trả lời bằng tiếng Việt, ngắn gọn, đúng trọng tâm."
)


def _plan_from_instance(instance):
    """Luồng engine cho input JSON có cấu trúc (demo/UI). L2 = heuristic (chưa có CP-SAT)."""
    call_model(SYSTEM, "Kiểm dữ liệu ca, lập bản nháp phân công và chờ trưởng ca duyệt.")
    issues = estimate_workload(instance)
    if issues:
        result = {"status": "need_info", "missing_fields": issues,
                  "warnings": ["Cần bổ sung dữ liệu; không suy ra task/kỹ năng từ staffing tổng hợp."]}
    else:
        result = solve_allocation(instance)
        if result["status"] == "draft":
            validation = validate_plan(instance, result)
            if validation["valid"]:
                result["validation"] = validation
                result["metrics"] = validation["metrics"]
                result["explanation"] = ("Đã kiểm kỹ năng, cửa giờ, tải, chuyển phòng, nghỉ và coverage "
                                         "theo input; trưởng ca duyệt trước khi áp dụng.")
            else:
                result = {"status": "unknown", "warnings": validation["violations"]}
    result.update(mode="cp3", approval_required=True)
    return {"output": json.dumps(result, ensure_ascii=False)}


def answer(text: str) -> dict:
    try:
        instance = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        instance = None
    if isinstance(instance, dict) and isinstance(instance.get("shift"), dict):
        return _plan_from_instance(instance)
    # Ngôn ngữ tự nhiên → model thật xử lý theo POLICY (đây là lời gọi AI quyết định hành vi).
    reply = call_model(POLICY, text if isinstance(text, str) else json.dumps(text, ensure_ascii=False))
    return {"output": reply["text"]}
