"""Công cụ CP2; chỉ xử lý dữ liệu, không áp dụng/gửi kế hoạch."""
from planning import draft_schedule, input_issues, validate_plan as check_plan
from tracing import tool


@tool
def estimate_workload(instance):
    """estimate_workload · input dict ca · output lỗi/giữ duration · không side effect.

    CP2 dùng duration đã cung cấp; chưa có lookup được duyệt để tự điền phút.
    """
    return input_issues(instance)


@tool
def solve_allocation(instance):
    """solve_allocation · input ca hợp lệ · output lịch heuristic CP2 · không side effect."""
    return draft_schedule(instance)


@tool
def validate_plan(instance, plan):
    """validate_plan · input ca+lịch · output hard checks/metrics · không side effect."""
    return check_plan(instance, plan)
