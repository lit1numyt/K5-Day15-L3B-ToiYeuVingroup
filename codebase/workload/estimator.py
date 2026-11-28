"""L3 · estimate_duration — điền est_duration_min có nguồn (docs/module-contract.md §3.3).

Hai lối vào:
- estimate_duration(instance) -> instance'  : đúng chữ ký contract. Không ước được thì
  raise DurationNeedInfo (có .missing_fields) để L1 hỏi lại; input hỏng thì InvalidInstance.
- assess_durations(instance) -> dict        : không raise, trả báo cáo đầy đủ.
  Schema báo cáo là ĐỀ XUẤT TẠM, cần thống nhất với L1 (Kiên) trước khi dùng chính thức.

L3 chỉ đọc/ghi hai trường est_duration_min và duration_source của task. Không tạo,
xóa hay sửa task, patient, nurse, required_skill, cửa giờ.
"""
import copy

from .features import build_features
from .models import (COMPLEXITY_FIELD, MOBILITY_SCOPE_FIELD, SETTING_FIELD, SIMMONS_SOURCE,
                     SINGLE_STAFF_FIELD, default_estimators, nonblank)

GIVEN = "given"
# Nguồn đang dùng trong fixture/bundle (given, provided_synthetic, Simmons). Contract chưa chốt whitelist:
# nguồn khác vẫn được GIỮ (không phá fixture) nhưng bị liệt kê ở "unverified_sources" + cảnh báo.
KNOWN_SOURCES = frozenset({GIVEN, "provided_synthetic", SIMMONS_SOURCE})
# L2/validator hiện giao đúng MỘT điều dưỡng cho mỗi task (planning.draft_schedule/validate_plan;
# input_issues đã chặn synchronization). Chỉ bật khi contract + L2 + validator cùng hỗ trợ.
MULTI_STAFF_SUPPORTED = False
CONDITION_TEXT_FIELDS = (MOBILITY_SCOPE_FIELD, SETTING_FIELD, COMPLEXITY_FIELD)


class DurationNeedInfo(Exception):
    """Còn task chưa có thời lượng có căn cứ; L1 cần hỏi lại missing_fields."""

    def __init__(self, missing_fields, report):
        super().__init__("; ".join(missing_fields))
        self.missing_fields = missing_fields
        self.report = report


class InvalidInstance(ValueError):
    """Instance sai cấu trúc tới mức L3 không đọc được task."""

    def __init__(self, issues, report):
        super().__init__("; ".join(issues))
        self.issues = issues
        self.report = report


def valid_minutes(value):
    """Số phút hợp lệ = int thật (không phải bool/float/str) và > 0."""
    return type(value) is int and value > 0


def structural_issues(instance):
    """Cấu trúc tối thiểu để L3 đọc an toàn. Không thay validator của L2 (planning.input_issues)."""
    if not isinstance(instance, dict):
        return ["input: cần JSON object"]
    issues = []
    if instance.get("shift") is not None and not isinstance(instance["shift"], dict):
        issues.append("shift: cần object")
    patients = instance.get("patients")
    if patients is not None:
        if not isinstance(patients, list):
            issues.append("patients: cần danh sách")
        else:
            seen = set()
            for index, patient in enumerate(patients):
                if not isinstance(patient, dict):
                    issues.append("patients[%d]: cần object" % index)
                elif not nonblank(patient.get("patient_id")):
                    issues.append("patients[%d].patient_id: cần chuỗi định danh" % index)
                elif patient["patient_id"] in seen:
                    issues.append("patients[%d].patient_id: trùng '%s'" % (index, patient["patient_id"]))
                else:
                    seen.add(patient["patient_id"])
    tasks = instance.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return issues + ["tasks: cần danh sách không rỗng"]
    seen = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            issues.append("tasks[%d]: cần object" % index)
            continue
        task_id = task.get("task_id")
        if not nonblank(task_id):
            issues.append("tasks[%d].task_id: cần mã định danh" % index)
        elif task_id in seen:
            issues.append("tasks[%d].task_id: trùng '%s'" % (index, task_id))
        else:
            seen.add(task_id)
        if task.get("patient_id") is not None and not nonblank(task["patient_id"]):
            issues.append("tasks[%d].patient_id: cần chuỗi định danh" % index)
    return issues


def condition_issues(task):
    """Kiểu dữ liệu trường điều kiện + giới hạn an toàn của hệ thống.

    Áp dụng cho MỌI task, kể cả task đã có duration: có phút không có nghĩa là xếp được.
    Không sửa staff_required/synchronization, chỉ báo để L1 hỏi lại.
    """
    prefix = "tasks." + task["task_id"]
    issues = []
    staff = task.get(SINGLE_STAFF_FIELD)
    if staff is not None:
        if type(staff) is not int or staff < 1:      # loại bool, float, chuỗi, list, dict, 0, âm
            issues.append("%s.%s: cần số nguyên dương (nhận %r)" % (prefix, SINGLE_STAFF_FIELD, staff))
        elif staff > 1 and not MULTI_STAFF_SUPPORTED:
            issues.append("%s.%s: task cần %d nhân viên đồng thời; L2/validator hiện chỉ giao một "
                          "điều dưỡng mỗi task, cần trưởng ca xác nhận cách xử lý" % (prefix, SINGLE_STAFF_FIELD, staff))
    for field in CONDITION_TEXT_FIELDS:
        value = task.get(field)
        if value is not None and not nonblank(value):
            issues.append("%s.%s: cần chuỗi không rỗng (nhận %r)" % (prefix, field, value))
    # Cùng quy ước truthy với planning.input_issues; contract chưa định nghĩa kiểu của trường này.
    if task.get("synchronization") and not MULTI_STAFF_SUPPORTED:
        issues.append(prefix + ".synchronization: cần đồng bộ nhiều nhân viên, L2/validator chưa hỗ trợ")
    return issues


def _estimate_one(task, features, estimators):
    """Trả (minutes, source, None) hoặc (None, None, [lý do cần bổ sung])."""
    prefix = "tasks." + task["task_id"]
    task_type = task.get("task_type")
    if not isinstance(task_type, str) or not task_type:
        return None, None, [prefix + ".task_type: cần loại công việc để ước lượng"]
    if not estimators:
        return None, None, [prefix + ".est_duration_min: cần thời lượng đã xác nhận "
                            "(L3 chưa có model/bảng tra được duyệt)"]
    candidates = [e for e in estimators if e.supports(task_type)]
    if not candidates:
        return None, None, [prefix + ".est_duration_min: task_type '%s' chưa được L3 hỗ trợ, "
                            "cần thời lượng đã xác nhận" % task_type]
    reasons = []
    for estimator in candidates:
        blocked = estimator.blockers(task)
        if blocked:
            reasons += blocked
            continue
        lacking = [f for f in estimator.required_features if f not in features]
        if lacking:
            reasons += ["%s.%s: cần để ước lượng (%s)" % (prefix, f, estimator.source) for f in lacking]
            continue
        minutes = estimator.predict(features)
        if minutes is None:
            reasons.append("%s.est_duration_min: %s không có giá trị cho tổ hợp feature này"
                           % (prefix, estimator.source))
            continue
        if not valid_minutes(minutes):
            reasons.append("%s.est_duration_min: %s trả giá trị không hợp lệ (%r), bỏ qua"
                           % (prefix, estimator.source, minutes))
            continue
        return minutes, estimator.source, None
    return None, None, sorted(set(reasons))


def assess_durations(instance, estimators=None):
    """Báo cáo ước lượng (schema đề xuất tạm):

    {"status": "ok" | "need_info" | "invalid_input",
     "instance": bản sao đã điền (chỉ khi ok) hoặc None,
     "estimated": [{"task_id", "est_duration_min", "duration_source"}],  # chỉ task L3 vừa điền
     "kept": [task_id đã có duration hợp lệ do input cung cấp],
     "unverified_sources": [task_id giữ nguồn ngoài KNOWN_SOURCES],
     "missing_fields": [...], "warnings": [...]}
    """
    explicit = None if estimators is None else tuple(estimators)
    report = {"status": "ok", "instance": None, "estimated": [], "kept": [],
              "unverified_sources": [], "missing_fields": [], "warnings": []}
    issues = structural_issues(instance)
    if issues:
        report.update(status="invalid_input", missing_fields=issues)
        return report

    result = copy.deepcopy(instance)
    patients = {p.get("patient_id"): p for p in result.get("patients") or [] if isinstance(p, dict)}
    shift = result.get("shift") if isinstance(result.get("shift"), dict) else {}
    missing = []
    for task in result["tasks"]:
        prefix = "tasks." + task["task_id"]
        value = task.get("est_duration_min")
        source = task.get("duration_source")       # None/không có = chưa cung cấp nguồn
        if source is not None and not nonblank(source):
            missing.append("%s.duration_source: giá trị không hợp lệ (%r), cần chuỗi nguồn "
                           "(given/lookup:…/model:…)" % (prefix, source))
            continue
        blocked = condition_issues(task)
        if blocked:
            missing += blocked
            continue
        if value is not None:
            if valid_minutes(value):
                # Giữ nguyên duration đã cho; chỉ gắn nhãn khi nguồn thiếu hoặc null.
                if source is None:
                    task["duration_source"] = GIVEN
                elif source not in KNOWN_SOURCES:
                    report["unverified_sources"].append(task["task_id"])
                report["kept"].append(task["task_id"])
            else:
                # Giá trị đã cho nhưng sai: không tự thay bằng ước lượng, hỏi lại người nhập.
                missing.append("%s.est_duration_min: giá trị đã cho không hợp lệ (%r), "
                               "cần số phút nguyên dương" % (prefix, value))
            continue
        if source is not None:
            missing.append(prefix + ".est_duration_min: có duration_source '%s' nhưng thiếu số phút"
                           % source)
            continue
        if explicit is None:
            explicit = default_estimators()   # chỉ đọc CSV khi thật sự cần tra
        features = build_features(task, patients.get(task.get("patient_id")), shift)
        minutes, source, reasons = _estimate_one(task, features, explicit)
        if reasons:
            missing += reasons
            continue
        task["est_duration_min"] = minutes
        task["duration_source"] = source
        report["estimated"].append({"task_id": task["task_id"], "est_duration_min": minutes,
                                    "duration_source": source})
    if missing:
        report.update(status="need_info", missing_fields=missing, estimated=[])
        report["warnings"].append("Chưa điền thời lượng cho ca này; cần bổ sung trước khi lập lịch.")
        return report
    # Chốt chặn cuối (không dùng assert vì python -O tắt assert): lỗi ở đây là lỗi nội bộ L3.
    incomplete = [t["task_id"] for t in result["tasks"]
                  if not (valid_minutes(t.get("est_duration_min")) and nonblank(t.get("duration_source")))]
    if incomplete:
        raise RuntimeError("L3 lỗi nội bộ: sắp trả task thiếu duration/nguồn: " + ", ".join(incomplete))
    if report["unverified_sources"]:
        report["warnings"].append("Giữ nguồn duration chưa có trong danh sách đã biết cho: "
                                  + ", ".join(report["unverified_sources"]) + "; cần trưởng ca/nhóm xác nhận.")
    report["instance"] = result
    return report


def estimate_duration(instance, estimators=None):
    """Seam contract L3: trả instance' (bản sao) với mọi task có est_duration_min + duration_source."""
    report = assess_durations(instance, estimators)
    if report["status"] == "invalid_input":
        raise InvalidInstance(report["missing_fields"], report)
    if report["status"] == "need_info":
        raise DurationNeedInfo(report["missing_fields"], report)
    return report["instance"]
