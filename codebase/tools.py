"""Planning tools; only return drafts and data, never apply/send a schedule."""
from planning import input_issues, validate_plan as check_plan
from tracing import tool


@tool
def estimate_workload(instance):
    """estimate_workload · input dict ca · output lỗi/giữ duration · không side effect.

    CP2 dùng duration đã cung cấp; chưa có lookup được duyệt để tự điền phút.
    """
    return input_issues(instance)


@tool
def solve_allocation(instance):
    """solve_allocation · input ca có duration · output CP-SAT plan · không side effect."""
    from cp_sat_engine import solve_allocation as solve
    return solve(instance)


@tool
def validate_plan(instance, plan):
    """validate_plan · input ca+lịch · output hard checks/metrics · không side effect."""
    return check_plan(instance, plan)
