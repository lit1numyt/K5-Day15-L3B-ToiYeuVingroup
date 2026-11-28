"""One-shift CP-SAT allocation; an independent oracle approves every draft.

Integer minutes, fixed nurse zones, one protected break per nurse. Patient/task
durations and policies are inputs, never inferred from taxonomy or benchmark IDs.
"""
import ortools
from ortools.sat.python import cp_model

from planning import input_issues, validate_plan

TIME_LIMIT_SECONDS = 10.0
RANDOM_SEED = 42
UTILIZATION_SCALE = 1000


def _result(status, warnings, **fields):
    return {"status": status, "approval_required": True, "method": "cp_sat",
            "warnings": warnings, **fields}


def solve_allocation(instance):
    """Return a checked draft, missing fields, a proof of infeasibility or unknown."""
    issues = input_issues(instance)
    if issues:
        return _result("need_info", ["Cần input và duration hợp lệ trước khi giải."],
                       missing_fields=issues)
    shift, nurses, tasks = instance["shift"], instance["nurses"], instance["tasks"]
    patients = {p["patient_id"]: p for p in instance["patients"]}
    horizon = shift["shift_length_min"]
    model = cp_model.CpModel()
    starts, ends, intervals, assigned = {}, {}, {}, {}
    for task in tasks:
        tid, duration = task["task_id"], task["est_duration_min"]
        starts[tid] = model.new_int_var(task["earliest_start"], horizon, "start_" + tid)
        ends[tid] = model.new_int_var(0, horizon, "end_" + tid)
        model.add(ends[tid] == starts[tid] + duration)
        model.add(ends[tid] <= task["deadline"])
        intervals[tid] = model.new_interval_var(starts[tid], duration, ends[tid], "task_" + tid)
        choices = []
        for nurse in nurses:
            if (patients[task["patient_id"]]["zone"] == nurse["home_zone"]
                    and set(task["required_skill"]).issubset(nurse["skills"])
                    and ("required_skill_level" not in task
                         or nurse["qualification_level"] >= task["required_skill_level"])):
                key = (nurse["nurse_id"], tid)
                assigned[key] = model.new_bool_var("assign_" + "_".join(key))
                choices.append(assigned[key])
                model.add(starts[tid] >= nurse["available_from"]).only_enforce_if(assigned[key])
                model.add(ends[tid] <= nurse["available_to"]).only_enforce_if(assigned[key])
        if not choices:
            return _result("infeasible", [tid + ": không nurse nào đủ skill/level/zone."])
        model.add_exactly_one(choices)
    # Input order is not a dependency order.
    for task in tasks:
        if task.get("precedence_task_id"):
            model.add(starts[task["task_id"]] >= ends[task["precedence_task_id"]])

    rests, loads = {}, {}
    travel_terms, group_terms = [], []
    policy = shift["break_policy"]
    break_duration = policy["duration_min"]

    def group(task):
        return task.get("compat_group_key") or (
            patients[task["patient_id"]]["room"], task["task_type"],
            tuple(sorted(task.get("equipment_required", []))),
        )

    for nurse in nurses:
        nid = nurse["nurse_id"]
        low = max(policy["window"][0], nurse["available_from"])
        high = min(policy["window"][1], nurse["available_to"]) - break_duration
        if low > high:
            return _result("infeasible", [nid + ": availability không chứa được giờ nghỉ bắt buộc."])
        rest_start = model.new_int_var(low, high, "break_" + nid)
        rest_interval = model.new_fixed_size_interval_var(rest_start, break_duration, "rest_" + nid)
        rests[nid] = (rest_start, rest_interval)
        timeline = [rest_interval]
        mine = [t for t in tasks if (nid, t["task_id"]) in assigned]
        work_terms = []
        for task in mine:
            tid = task["task_id"]
            present = assigned[nid, tid]
            timeline.append(model.new_optional_interval_var(
                starts[tid], task["est_duration_min"], ends[tid], present, "work_" + nid + "_" + tid
            ))
            work_terms.append(task["est_duration_min"] * present)
        nurse_travel = []
        if mine:
            empty = model.new_bool_var("empty_" + nid)
            model.add(sum(assigned[nid, t["task_id"]] for t in mine) == 0).only_enforce_if(empty)
            model.add(sum(assigned[nid, t["task_id"]] for t in mine) >= 1).only_enforce_if(empty.Not())
            arcs = [(0, 0, empty)]
            for i, task in enumerate(mine, 1):
                tid = task["task_id"]
                arcs.extend([
                    (i, i, assigned[nid, tid].Not()),
                    (0, i, model.new_bool_var(f"first_{nid}_{i}")),
                    (i, 0, model.new_bool_var(f"last_{nid}_{i}")),
                ])
                for j, following in enumerate(mine, 1):
                    if i == j:
                        continue
                    next_id = following["task_id"]
                    active = model.new_bool_var(f"next_{nid}_{i}_{j}")
                    arcs.append((i, j, active))
                    travel = shift["room_switch_min"] if (
                        patients[task["patient_id"]]["room"]
                        != patients[following["patient_id"]]["room"]
                    ) else 0
                    model.add(starts[next_id] >= ends[tid] + travel).only_enforce_if(active)
                    if travel:
                        model.add(starts[next_id] - travel >= nurse["available_from"]).only_enforce_if(active)
                        timeline.append(model.new_optional_interval_var(
                            starts[next_id] - travel, travel, starts[next_id], active,
                            f"travel_{nid}_{i}_{j}",
                        ))
                        nurse_travel.append(travel * active)
                    if group(task) != group(following):
                        group_terms.append(active)
            model.add_circuit(arcs)
        model.add_no_overlap(timeline)
        loads[nid] = model.new_int_var(0, min(horizon, nurse["max_capacity_min"]), "load_" + nid)
        model.add(loads[nid] == sum(work_terms) + sum(nurse_travel))
        travel_terms.extend(nurse_travel)

    for index, rule in enumerate(shift["coverage_rules"]):
        eligible = [n for n in nurses if n["home_zone"] == rule["zone"]
                    and (rule["required_skill"] is None or rule["required_skill"] in n["skills"])]
        if rule["min_staff"] > len(eligible):
            return _result("infeasible", [f"coverage rule {index}: không đủ người đúng zone/skill."])
        off_duty = [rests[n["nurse_id"]][1] for n in eligible]
        for nurse in eligible:
            for label, start, end in [
                ("before", 0, nurse["available_from"]),
                ("after", nurse["available_to"], horizon),
            ]:
                if end > start:
                    off_duty.append(model.new_fixed_size_interval_var(
                        start, end - start, f"off_{index}_{nurse['nurse_id']}_{label}"
                    ))
        # Outside this rule's window only unavailable/rest intervals consume capacity.
        # Within it, reserving min_staff leaves at most N-min_staff off duty.
        reserve = model.new_fixed_size_interval_var(
            rule["start"], rule["end"] - rule["start"], f"coverage_{index}"
        )
        model.add_cumulative(off_duty + [reserve], [1] * len(off_duty) + [rule["min_staff"]], len(eligible))

    for resource, capacity in shift.get("equipment_capacity", {}).items():
        resource_tasks = [intervals[t["task_id"]] for t in tasks if resource in t.get("equipment_required", [])]
        if resource_tasks:
            model.add_cumulative(resource_tasks, [1] * len(resource_tasks), capacity)

    utilizations = []
    for nurse in nurses:
        utilization = model.new_int_var(0, UTILIZATION_SCALE, "util_" + nurse["nurse_id"])
        capacity = nurse["max_capacity_min"]
        model.add_division_equality(
            utilization, loads[nurse["nurse_id"]] * UTILIZATION_SCALE + capacity - 1, capacity
        )
        utilizations.append(utilization)
    peak = model.new_int_var(0, UTILIZATION_SCALE, "peak_utilization")
    model.add_max_equality(peak, utilizations)
    differences = []
    for i, first in enumerate(utilizations):
        for j in range(i + 1, len(utilizations)):
            delta = model.new_int_var(0, UTILIZATION_SCALE, f"deviation_{i}_{j}")
            model.add_abs_equality(delta, first - utilizations[j])
            differences.append(delta)
    # Bounded lexicographic priorities: peak, pairwise utilization spread, then
    # transition minutes + group changes. These are engineering objectives, not CV.
    minor_bound = horizon * len(nurses) + len(tasks)
    spread_bound = UTILIZATION_SCALE * len(differences)
    spread_weight = minor_bound + 1
    peak_weight = (spread_bound + 1) * spread_weight
    model.minimize(peak * peak_weight + sum(differences) * spread_weight
                   + sum(travel_terms) + sum(group_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIME_LIMIT_SECONDS
    solver.parameters.random_seed = RANDOM_SEED
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    if status == cp_model.MODEL_INVALID:
        raise RuntimeError("CP-SAT MODEL_INVALID: " + model.validate())
    diagnostics = {"name": "CP-SAT", "version": ortools.__version__,
                   "status": solver.status_name(status), "wall_time_s": solver.wall_time,
                   "time_limit_s": TIME_LIMIT_SECONDS, "seed": RANDOM_SEED, "workers": 1}
    if status == cp_model.INFEASIBLE:
        return _result("infeasible", ["CP-SAT chứng minh mô hình không có lịch thỏa input."], solver=diagnostics)
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return _result("unknown", ["CP-SAT dừng mà chưa có nghiệm khả thi; không kết luận vô nghiệm."], solver=diagnostics)
    diagnostics.update(objective=solver.objective_value, best_bound=solver.best_objective_bound)
    assignments = []
    for (nid, tid), present in assigned.items():
        if solver.boolean_value(present):
            assignments.append({"task_id": tid, "nurse_id": nid,
                                "start": solver.value(starts[tid]), "end": solver.value(ends[tid])})
    breaks = [{"nurse_id": nid, "start": solver.value(start),
               "end": solver.value(start) + break_duration} for nid, (start, _) in rests.items()]
    plan = _result("draft", [], assignments=sorted(assignments, key=lambda a: (a["nurse_id"], a["start"])),
                   breaks=breaks, unassigned_tasks=[], solver=diagnostics)
    validation = validate_plan(instance, plan)
    if not validation["valid"]:
        return _result("unknown", validation["violations"], solver=diagnostics)
    plan.update(validation=validation, metrics=validation["metrics"],
                explanation="CP-SAT lập nháp theo skill/level, cửa giờ, capacity, coverage và nghỉ đã cho; validator kiểm lại. Trưởng ca duyệt trước khi áp dụng.")
    return plan
