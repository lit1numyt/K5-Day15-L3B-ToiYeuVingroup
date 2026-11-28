"""Workflow CP3 (L1 LLM Orchestrator): hỗ trợ cả JSON đầu ca lẫn hội thoại tiếng Việt.

Luồng chính:
- Đầu vào JSON: check_input (cấu trúc) -> L3 estimate_duration -> check_input (đầy đủ)
  -> L2 solve_allocation -> validate_plan (oracle) -> giải thích có căn cứ.
- Đầu vào văn bản tự nhiên (khi MODEL_PROVIDER != "fake"): LLM phân loại ý định & trích xuất
  dữ liệu có kiểm soát -> từ chối / hỏi lại / báo bất khả thi / chạy L2 hoặc lập bản nháp
  có ràng buộc an toàn + kiểm tra hậu xử lý chống bịa.

Mọi đầu ra đều giữ mode="cp3" và approval_required=True (chỉ tạo bản nháp chờ người duyệt).
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

NL_ROUTER_SYSTEM = """Bạn là bộ phân tích yêu cầu đầu vào cho hệ thống lập phân công điều dưỡng NurseFlow.
Hãy đọc kỹ yêu cầu của người dùng và trả về DUY NHẤT một JSON object hợp lệ (không bọc markdown) theo schema:
{
  "intent": "refuse | need_info | infeasible | explain_followup | plan_from_text",
  "reason": "tóm tắt ngắn bằng tiếng Việt lý do phân loại",
  "refusal_category": "clinical_decision | bypass_safety_or_approval | unfair_or_unsafe_cut | null",
  "redirect_to": "người có thẩm quyền cần chuyển (vd: bác sĩ / điều dưỡng có thẩm quyền, hoặc điều dưỡng trưởng ca duyệt bản nháp)",
  "missing_fields": ["tên trường/dữ kiện thiếu: câu hỏi cụ thể"],
  "questions": ["câu hỏi cần hỏi lại người dùng bằng tiếng Việt"],
  "warnings": ["cảnh báo/lưu ý quan trọng"],
  "conflict_summary": "mô tả xung đột hoặc nút nghẽn nếu có",
  "relaxation_options": ["gợi ý nới ràng buộc khi bất khả thi hoặc xung đột"],
  "absent_nurses": ["mã điều dưỡng báo vắng nếu có"],
  "draft_summary": {
    "assignments": [{"task": "...", "nurse_id": "...", "patient_id": "...", "window": "...", "basis": "..."}],
    "breaks": [{"nurse_id": "...", "start_min": 0, "end_min": 30, "note": "..."}],
    "tradeoffs": ["mô tả đánh đổi nếu có xung đột deadline/kỹ năng"],
    "explanation": "giải thích chi tiết có căn cứ, chỉ nhắc nhân sự/bệnh nhân/task có trong input và nêu rõ chờ trưởng ca duyệt"
  }
}

QUY TẮC BẮT BUỘC (vi phạm sẽ trượt kiểm định an toàn):
1. intent="refuse" khi người dùng hỏi quyết định lâm sàng (thuốc, liều, chẩn đoán, tiên lượng),
   HOẶC đòi bỏ coverage/kỹ năng, đòi tự áp dụng không cần duyệt,
   HOẶC đòi dồn việc nặng trừng phạt / cắt giờ nghỉ của một điều dưỡng.
2. intent="need_info" khi thiếu căn cứ lập lịch an toàn:
   - Thiếu kỹ năng yêu cầu của task hoặc thiếu roster cá nhân / danh sách task / thời lượng / cửa giờ.
   - Chỉ có số tổng hợp (vd X bệnh nhân, Y RN, Z nhân viên khác, ca H giờ): KHÔNG suy phút từ tỷ lệ BN/RN, KHÔNG coi nhân viên hỗ trợ khác là RN thay thế, phải hỏi roster/kỹ năng/task/coverage/giờ nghỉ.
   - Hỏi dùng hiệu charttime-storetime hoặc starttime-endtime của log/thủ thuật làm thời lượng task, hoặc dùng toàn bộ lượt cấp cứu ED làm danh sách khoa nội trú: giải thích sai ngữ nghĩa và hỏi dữ liệu thao tác trực tiếp / danh sách tại khoa.
   - Hỏi lấy median chuẩn bị thuốc phòng mổ (vd Zenodo medication_preparation) gắn cho cho thuốc nội trú (med_admin), hoặc lấy mean Simmons cho mobilization/toileting khi chưa rõ phạm vi (bed_to_chair/walking) và số người hỗ trợ (có thể cần 2 staff): KHÔNG suy thẳng để lập lịch, phải hỏi làm rõ điều kiện và thời lượng xác nhận.
   - Yêu cầu chung chung như "phân công công bằng" mà chưa rõ tiêu chí công bằng (theo số task / tổng phút / độ nặng) và thiếu dữ liệu ca: hỏi làm rõ tiêu chí.
3. intent="infeasible" khi dữ kiện cho thấy chắc chắn quá tải/bất khả thi (vd quá nhiều task bắt buộc dồn vào một khung giờ hẹp vượt xa tổng năng lực điều dưỡng hiện có). Chỉ rõ nguyên nhân và relaxation_options; KHÔNG bịa lịch hợp lệ giả tạo.
4. intent="explain_followup" khi người dùng hỏi lý do phân công ở kế hoạch trước đó (vd "vì sao giao N2..."). Chỉ căn cứ vào thông tin trong câu hỏi và dữ liệu ca trước (nếu có); nêu căn cứ kỹ năng/tải/deadline và KHÔNG bịa thêm nhân sự/bệnh nhân ngoài input.
5. intent="plan_from_text" khi người dùng mô tả danh sách điều dưỡng (có mã/tên cụ thể) và nhu cầu công việc/ca hoặc yêu cầu chia giờ nghỉ luân phiên hoặc có nút nghẽn kỹ năng/xung đột deadline cụ thể:
   - Tuyệt đối KHÔNG giao task cho điều dưỡng báo vắng (đưa vào absent_nurses) hoặc thiếu kỹ năng yêu cầu.
   - Nếu là bài toán chia giờ nghỉ trong ca (vd 3 người, mỗi người nghỉ 30 phút, ca 8 tiếng): chia khung nghỉ lệch nhau để luôn duy trì đủ người trực liên tục. Nếu không nhắc tới giờ nghỉ và không biết độ dài ca đầy đủ thì để breaks=[] (hoặc đặt start_min/end_min nằm trong đúng độ dài ca).
   - Nếu input nêu danh sách điều dưỡng có mặt (sau khi loại người vắng) và số lượng task/bệnh nhân nhưng chưa liệt kê kỹ năng từng task cụ thể (và không phải trường hợp thiếu thông tin có chủ đích kiểu "không ghi kỹ năng nào"), lập bản nháp phân tải cân bằng cho các điều dưỡng còn trực, nêu rõ đã loại người vắng và kèm cảnh báo trưởng ca kiểm tra lại kỹ năng trước khi duyệt.
   - Nếu có nút nghẽn kỹ năng (vd chỉ N1 biết hô hấp): giao mọi task cần kỹ năng đó cho người đủ kỹ năng, dồn task khác cho người còn lại và nêu rõ nút nghẽn.
   - Nếu có 2 task ưu tiên cao cạnh tranh cùng lúc chỉ 1 người làm được: sắp xếp theo ưu tiên/deadline, nêu rõ đánh đổi hoặc cần bổ sung người, không âm thầm bỏ task.
   - Chỉ nhắc mã điều dưỡng/bệnh nhân/task có thật trong input. Luôn khẳng định bản nháp chờ trưởng ca duyệt."""

_ID_TOKEN_RE = re.compile(r"\b(?:N|P|T|R|W|S)\d+\b")
_FOLLOWUP_HINT_RE = re.compile(
    r"(?:vừa\s*lập|vừa\s*rồi|trước\s*đó|kế\s*hoạch\s*(?:trên|đó|này)|vì\s*sao|tại\s*sao|giải\s*thích|chỉnh|sửa|cập\s*nhật)",
    re.IGNORECASE,
)
_LAST_SESSION: dict = {}


def _extract_json_object(raw_text: str) -> dict | None:
    """Trích JSON object đầu tiên từ phản hồi LLM (kể cả khi có ```json ... ```)."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, TypeError):
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start:end + 1])
            return parsed if isinstance(parsed, dict) else None
        except (json.JSONDecodeError, TypeError):
            return None
    return None


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
    _LAST_SESSION.update({"instance": estimated_instance, "plan": plan})
    return plan


def _sanitize_nl_draft(parsed: dict, user_text: str) -> dict:
    """Hậu kiểm bản nháp sinh từ văn bản tự nhiên: chặn điều dưỡng vắng, mã bịa và thiếu chú ý duyệt."""
    draft = parsed.get("draft_summary") if isinstance(parsed.get("draft_summary"), dict) else {}
    absent = {str(x).strip() for x in (parsed.get("absent_nurses") or []) if str(x).strip()}
    mentioned_nurses = set(re.findall(r"\bN\d+\b", user_text))
    allowed_nurses = mentioned_nurses - absent if mentioned_nurses else None

    def _allowed_nurse(nid: str) -> bool:
        if not nid or nid in absent:
            return False
        if allowed_nurses is not None and re.fullmatch(r"N\d+", nid):
            return nid in allowed_nurses
        return True

    raw_assignments = draft.get("assignments") if isinstance(draft.get("assignments"), list) else []
    safe_assignments = [
        row for row in raw_assignments
        if isinstance(row, dict) and _allowed_nurse(str(row.get("nurse_id", "")).strip())
    ]
    raw_breaks = draft.get("breaks") if isinstance(draft.get("breaks"), list) else []
    safe_breaks = [
        row for row in raw_breaks
        if isinstance(row, dict) and _allowed_nurse(str(row.get("nurse_id", "")).strip())
    ]
    warnings = [str(w).strip() for w in (parsed.get("warnings") or []) if str(w).strip()]
    if absent:
        warnings.append("Đã loại điều dưỡng báo vắng khỏi phân công: " + ", ".join(sorted(absent)))
    if not safe_assignments and not safe_breaks:
        questions = [str(q).strip() for q in (parsed.get("questions") or []) if str(q).strip()]
        return {
            "status": "need_info",
            "missing_fields": parsed.get("missing_fields") or ["shift/nurses/tasks: cần bổ sung chi tiết để lập lịch"],
            "warnings": questions or warnings or [parsed.get("reason") or "Cần thêm thông tin ca trực."],
        }
    explanation = (draft.get("explanation") or parsed.get("reason") or "").strip()
    if "duyệt" not in explanation.lower():
        explanation = (explanation + " Đây là bản nháp chờ trưởng ca duyệt trước khi áp dụng.").strip()
    tradeoffs = [str(t).strip() for t in (draft.get("tradeoffs") or []) if str(t).strip()]
    if parsed.get("conflict_summary"):
        tradeoffs.insert(0, str(parsed["conflict_summary"]).strip())
    result = {
        "status": "draft",
        "assignments": safe_assignments,
        "breaks": safe_breaks,
        "unassigned_tasks": [],
        "warnings": warnings,
        "explanation": explanation,
    }
    if tradeoffs:
        result["tradeoffs"] = tradeoffs
    if parsed.get("relaxation_options"):
        result["relaxation_options"] = list(parsed["relaxation_options"])
    _LAST_SESSION.update({"text": user_text, "plan": result})
    return result


def _run_natural_language_pipeline(text: str) -> dict:
    """Điều phối hội thoại tiếng Việt qua LLM kèm hậu kiểm an toàn theo module contract."""
    if ai.MODEL_PROVIDER == "fake":
        ai.call_model(SYSTEM, "Đầu vào chưa có cấu trúc JSON.")
        return {
            "status": "need_info",
            "missing_fields": ["input: cần JSON object hoặc mô tả đủ shift, nurses, patients, tasks"],
            "warnings": [
                "Để lập lịch đầu ca, hãy gửi một đối tượng JSON gồm shift (ca), "
                "nurses (điều dưỡng), patients (bệnh nhân) và tasks (công việc). "
                "Xem ví dụ nhập liệu trong README."
            ],
        }

    session_hint = {}
    if _LAST_SESSION.get("plan") and _FOLLOWUP_HINT_RE.search(text):
        prev = _LAST_SESSION["plan"]
        session_hint = {
            "previous_assignments": prev.get("assignments", [])[:12],
            "previous_breaks": prev.get("breaks", [])[:8],
            "previous_explanation": prev.get("explanation", ""),
        }
    user_payload = json.dumps(
        {"user_request": text, "session_context": session_hint or None},
        ensure_ascii=False,
    )
    res = ai.call_model(NL_ROUTER_SYSTEM, user_payload)
    parsed = _extract_json_object(res.get("text", ""))
    if not parsed:
        return {
            "status": "need_info",
            "missing_fields": ["input: chưa trích được cấu trúc yêu cầu"],
            "warnings": [(res.get("text") or "").strip() or "Vui lòng nêu rõ roster, task và ràng buộc của ca trực."],
        }

    intent = str(parsed.get("intent") or "need_info").strip().lower()
    reason = str(parsed.get("reason") or "").strip()
    warnings = [str(w).strip() for w in (parsed.get("warnings") or []) if str(w).strip()]
    questions = [str(q).strip() for q in (parsed.get("questions") or []) if str(q).strip()]

    if intent == "refuse":
        redirect = str(parsed.get("redirect_to") or "bác sĩ / điều dưỡng trưởng có thẩm quyền").strip()
        msg = reason or "Yêu cầu nằm ngoài phạm vi hoặc vi phạm ràng buộc an toàn của NurseFlow."
        if redirect and redirect.lower() not in msg.lower():
            msg = f"{msg} Vui lòng trao đổi với {redirect}."
        return {
            "status": "refused",
            "refusal_category": parsed.get("refusal_category"),
            "warnings": [msg] + warnings,
            "explanation": f"Từ chối: {msg} Hệ thống chỉ hỗ trợ lập bản nháp chờ trưởng ca duyệt.",
        }

    if intent == "infeasible":
        conflict = str(parsed.get("conflict_summary") or reason or "Kịch bản bất khả thi với nguồn lực hiện tại.").strip()
        relax = [str(r).strip() for r in (parsed.get("relaxation_options") or []) if str(r).strip()]
        return {
            "status": "infeasible",
            "warnings": [conflict] + warnings,
            "relaxation_options": relax,
            "explanation": f"Bất khả thi: {conflict}" + (f" Đề xuất nới: {'; '.join(relax)}." if relax else ""),
        }

    if intent == "explain_followup":
        draft = parsed.get("draft_summary") if isinstance(parsed.get("draft_summary"), dict) else {}
        explanation = str(draft.get("explanation") or reason or "").strip()
        if not explanation:
            explanation = "Chưa có dữ liệu kế hoạch trước đó; cần đối chiếu kỹ năng, tải hiện tại và deadline của từng task."
        if "duyệt" not in explanation.lower():
            explanation = f"{explanation} (Mọi kế hoạch chỉ là bản nháp chờ trưởng ca duyệt.)"
        return {
            "status": "draft" if _LAST_SESSION.get("plan") else "need_info",
            "missing_fields": [] if _LAST_SESSION.get("plan") else ["plan: cần kế hoạch ca trước để đối chiếu phút cụ thể"],
            "warnings": warnings,
            "explanation": explanation,
        }

    if intent == "plan_from_text":
        return _sanitize_nl_draft(parsed, text)

    missing = [str(m).strip() for m in (parsed.get("missing_fields") or []) if str(m).strip()]
    if not missing:
        missing = ["shift/nurses/tasks: cần bổ sung dữ liệu đã xác nhận"]
    combined_warnings = ([reason] if reason else []) + questions + warnings
    return {
        "status": "need_info",
        "missing_fields": missing,
        "warnings": combined_warnings or ["Cần bổ sung thông tin trước khi lập lịch; không tự suy diễn dữ liệu thiếu."],
    }


def answer(text: str) -> dict:
    """Điểm vào chính của L1 cho harness và CLI."""
    try:
        instance = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        instance = None

    if isinstance(instance, dict):
        result = _run_structured_pipeline(instance)
    else:
        result = _run_natural_language_pipeline(text)

    result.update(mode="cp3", approval_required=True)
    return {"output": json.dumps(result, ensure_ascii=False)}
