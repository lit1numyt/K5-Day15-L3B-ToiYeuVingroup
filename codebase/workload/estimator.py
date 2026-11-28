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
from .models import default_estimators

GIVEN = "given"


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
    if not isinstance(instance, dict):
        return ["input: cần JSON object"]
    tasks = instance.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return ["tasks: cần danh sách không rỗng"]
    issues = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            issues.append("tasks[%d]: cần object" % index)
            continue
        if not isinstance(task.get("task_id"), str) or not task["task_id"]:
            issues.append("tasks[%d].task_id: cần mã định danh" % index)
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
     "kept": [task_id đã có duration hợp lệ],
     "missing_fields": [...], "warnings": [...]}
    """
    explicit = None if estimators is None else tuple(estimators)
    report = {"status": "ok", "instance": None, "estimated": [], "kept": [],
              "missing_fields": [], "warnings": []}
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
        source = task.get("duration_source")
        if source is not None and (not isinstance(source, str) or not source.strip()):
            missing.append("%s.duration_source: giá trị không hợp lệ (%r), cần chuỗi nguồn "
                           "(given/lookup:…/model:…)" % (prefix, source))
            continue
        if value is not None:
            if valid_minutes(value):
                # Giữ nguyên duration đã cho; chỉ gắn nhãn nguồn khi input chưa ghi.
                task.setdefault("duration_source", GIVEN)
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
    # Chốt chặn cuối: không bao giờ trả instance còn task thiếu phút/nguồn cho solver.
    assert all(valid_minutes(t.get("est_duration_min")) and t.get("duration_source")
               for t in result["tasks"]), "L3 sắp trả instance thiếu duration"
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
