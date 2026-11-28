"""Công cụ điều phối NurseFlow; chỉ xử lý dữ liệu và tạo bản nháp, không side effect ra ngoài."""
from planning import draft_schedule, input_issues, validate_plan as check_plan
from tracing import tool
from workload import estimate_duration as l3_estimate_duration

_DURATION_MISSING_SUFFIX = ".est_duration_min: cần duration được cung cấp/xác nhận"


@tool
def check_input(instance, require_duration: bool = True):
    """check_input · input (instance dict, require_duration bool) · output list[str] lỗi thiếu trường · không side effect."""
    issues = input_issues(instance)
    if require_duration:
        return issues
    return [issue for issue in issues if not issue.endswith(_DURATION_MISSING_SUFFIX)]


@tool
def estimate_duration(instance):
    """estimate_duration · input instance dict · output bản sao instance đủ est_duration_min + duration_source · không side effect."""
    return l3_estimate_duration(instance)


@tool
def solve_allocation(instance):
    """solve_allocation · input instance hợp lệ · output lịch dự thảo L2 · không side effect."""
    return draft_schedule(instance)


@tool
def validate_plan(instance, plan):
    """validate_plan · input (instance, plan) · output {valid, violations, metrics} · không side effect."""
    return check_plan(instance, plan)
