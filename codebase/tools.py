"""Công cụ điều phối NurseFlow; chỉ xử lý dữ liệu và tạo bản nháp, không side effect ra ngoài."""
from planning import input_issues, validate_plan as check_plan
from tracing import tool
from workload import estimate_duration as l3_estimate_duration


@tool
def check_input(instance, require_duration: bool = True):
    """check_input · input (instance dict, require_duration bool) · output list[str] lỗi thiếu trường · không side effect."""
    return input_issues(instance, require_duration=require_duration)


@tool
def estimate_duration(instance):
    """estimate_duration · input instance dict · output bản sao instance đủ est_duration_min + duration_source · không side effect."""
    return l3_estimate_duration(instance)


@tool
def solve_allocation(instance):
    """solve_allocation · input instance hợp lệ · output lịch dự thảo L2 · không side effect."""
    from cp_sat_engine import solve_allocation as solve
    return solve(instance)


@tool
def validate_plan(instance, plan):
    """validate_plan · input (instance, plan) · output {valid, violations, metrics} · không side effect."""
    return check_plan(instance, plan)
