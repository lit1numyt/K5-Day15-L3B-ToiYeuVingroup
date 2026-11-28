"""Input checks and independent planning validator; no external side effects."""
import statistics


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def interval(start, end, horizon):
    return integer(start) and integer(end) and 0 <= start < end <= horizon


def overlap(a, b):
    return max(a[0], b[0]) < min(a[1], b[1])


def input_issues(instance, *, require_duration=True):
    """Trả tên dữ liệu cần bổ sung; không suy diễn kỹ năng/y lệnh/thời lượng."""
    if not isinstance(instance, dict):
        return ["input: cần JSON object"]
    errors = []
    shift = instance.get("shift")
    if not isinstance(shift, dict):
        return ["shift: cần mô tả ca", "nurses: cần roster cá nhân", "tasks: cần danh sách việc"]
    horizon = shift.get("shift_length_min")
    if not integer(horizon, 1):
        return ["shift.shift_length_min: cần số phút nguyên dương"]
    if horizon > 1440:
        return ["Hỗ trợ một ca tối đa 1440 phút"]
    for key in ("shift_id", "ward_id"):
        if not isinstance(shift.get(key), str) or not shift[key].strip():
            errors.append("shift." + key + ": cần mã định danh")
    for entity, key in [("nurses", "nurse_id"), ("patients", "patient_id"), ("tasks", "task_id")]:
        rows = instance.get(entity)
        if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
            errors.append(entity + ": cần danh sách không rỗng")
            continue
        ids = [r.get(key) for r in rows]
        if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(map(str, ids))) != len(ids):
            errors.append(entity + ": ID thiếu/trùng")
    if errors:
        return errors
    policy = shift.get("break_policy", {})
    window = policy.get("window") if isinstance(policy, dict) else None
    if not (isinstance(window, list) and len(window) == 2 and interval(*window, horizon)
            and integer(policy.get("duration_min"), 1)
            and policy["duration_min"] <= window[1] - window[0]):
        errors.append("shift.break_policy: cần độ dài/cửa nghỉ hợp lệ")
    if isinstance(policy, dict) and policy.get("blocks"):
        errors.append("shift.break_policy.blocks: chưa hỗ trợ nhiều block nghỉ")
    if not integer(shift.get("room_switch_min")):
        errors.append("shift.room_switch_min: cần số phút nguyên không âm")
    equipment = shift.get("equipment_capacity", {})
    if not (isinstance(equipment, dict) and all(
            isinstance(key, str) and key.strip() and integer(value, 1)
            for key, value in equipment.items())):
        errors.append("shift.equipment_capacity: cần ID và capacity nguyên dương")
        equipment = {}
    if shift.get("phase_structure"):
        errors.append("shift.phase_structure: cần biểu diễn bằng task windows/precedence")
    rules = shift.get("coverage_rules")
    if not isinstance(rules, list) or not rules:
        errors.append("shift.coverage_rules: cần quy tắc coverage")
    else:
        for rule in rules:
            if not (isinstance(rule, dict) and interval(rule.get("start"), rule.get("end"), horizon)
                    and integer(rule.get("min_staff")) and isinstance(rule.get("zone"), str)
                    and rule["zone"].strip()
                    and "required_skill" in rule
                    and (rule["required_skill"] is None
                         or (isinstance(rule["required_skill"], str) and rule["required_skill"].strip()))):
                errors.append("shift.coverage_rules: quy tắc không hợp lệ")
    for nurse in instance["nurses"]:
        if nurse.get("shift_id", shift["shift_id"]) != shift["shift_id"]:
            errors.append("nurses.%s.shift_id: khác ca" % nurse["nurse_id"])
        if not (isinstance(nurse.get("skills"), list) and nurse["skills"]
                and all(isinstance(s, str) and s.strip() for s in nurse["skills"])
                and isinstance(nurse.get("home_zone"), str) and nurse["home_zone"].strip()
                and interval(nurse.get("available_from"), nurse.get("available_to"), horizon)
                and integer(nurse.get("max_capacity_min"), 1)):
            errors.append("nurses.%s: cần skill, zone, availability, capacity" % nurse["nurse_id"])
    patients = {p["patient_id"]: p for p in instance["patients"]}
    for patient in patients.values():
        if patient.get("ward_id", shift["ward_id"]) != shift["ward_id"]:
            errors.append("patients.%s.ward_id: khác khoa" % patient["patient_id"])
        if not all(isinstance(patient.get(k), str) and patient[k].strip() for k in ("room", "zone")):
            errors.append("patients.%s: cần room/zone" % patient["patient_id"])
    task_ids = {task["task_id"] for task in instance["tasks"]}
    predecessors = {}
    for task in instance["tasks"]:
        prefix = "tasks." + task["task_id"]
        if task.get("synchronization"):
            errors.append(prefix + ".synchronization: chưa hỗ trợ, cần review")
        if any(task.get(key) for key in ("status", "locked", "completed", "in_progress")):
            errors.append(prefix + ": cần schema trạng thái/locked trước khi lập lại giữa ca")
        if "staff_required" in task and not (type(task["staff_required"]) is int and task["staff_required"] == 1):
            errors.append(prefix + ".staff_required: schema hiện chỉ hỗ trợ một người mỗi task")
        predecessor = task.get("precedence_task_id")
        if predecessor is not None:
            if not isinstance(predecessor, str) or predecessor not in task_ids or predecessor == task["task_id"]:
                errors.append(prefix + ".precedence_task_id: cần ID task trước hợp lệ")
            else:
                predecessors[task["task_id"]] = predecessor
        resources = task.get("equipment_required", [])
        if not (isinstance(resources, list)
                and all(isinstance(e, str) and e in equipment for e in resources)
                and len(resources) == len(set(map(str, resources)))):
            errors.append(prefix + ".equipment_required: cần ID duy nhất và capacity đã cho")
        if ((require_duration or "est_duration_min" in task)
                and not integer(task.get("est_duration_min"), 1)):
            errors.append(prefix + ".est_duration_min: cần duration được cung cấp/xác nhận")
        if not (isinstance(task.get("required_skill"), list) and task["required_skill"]
                and all(isinstance(s, str) and s.strip() for s in task["required_skill"])):
            errors.append(prefix + ".required_skill: cần kỹ năng đã xác nhận")
        if not interval(task.get("earliest_start"), task.get("deadline"), horizon):
            errors.append(prefix + ": cần earliest_start/deadline hợp lệ")
        if (not isinstance(task.get("patient_id"), str) or task["patient_id"] not in patients
                or task.get("mandatory") is not True):
            errors.append(prefix + ": cần patient_id/mandatory hợp lệ")
        if not isinstance(task.get("task_type"), str) or not task["task_type"].strip():
            errors.append(prefix + ".task_type: cần loại công việc")
        if "required_skill_level" in task:
            if not integer(task["required_skill_level"]) or any(
                    not integer(n.get("qualification_level")) for n in instance["nurses"]):
                errors.append(prefix + ": cần qualification_level để kiểm required_skill_level")
        if "compat_group_key" in task and not isinstance(task["compat_group_key"], str):
            errors.append(prefix + ".compat_group_key: cần chuỗi")
    for task_id in predecessors:
        visited = set()
        cursor = task_id
        while cursor in predecessors:
            if cursor in visited:
                errors.append("tasks.precedence_task_id: chu trình không hợp lệ")
                break
            visited.add(cursor)
            cursor = predecessors[cursor]
    return errors


def validate_plan(instance, plan):
    """Tính lại hard checks và metrics từ input/lịch, không tin flag của LLM."""
    errors = input_issues(instance)
    if errors:
        return {"valid": False, "violations": errors, "metrics": {}}
    if not isinstance(plan, dict) or plan.get("status") != "draft" or plan.get("approval_required") is not True:
        return {"valid": False, "violations": ["plan phải là draft chờ duyệt"], "metrics": {}}
    assignments, breaks = plan.get("assignments"), plan.get("breaks")
    if not (isinstance(assignments, list) and isinstance(breaks, list)
            and all(isinstance(a, dict) for a in assignments + breaks)):
        return {"valid": False, "violations": ["assignments/breaks không hợp lệ"], "metrics": {}}
    if any(not isinstance(a.get("task_id"), str) for a in assignments) or any("task_id" in b for b in breaks):
        return {"valid": False, "violations": ["assignment phải có task_id; break không được chứa task_id"], "metrics": {}}
    shift = instance["shift"]
    horizon = shift["shift_length_min"]
    nurses = {n["nurse_id"]: n for n in instance["nurses"]}
    tasks = {t["task_id"]: t for t in instance["tasks"]}
    patients = {p["patient_id"]: p for p in instance["patients"]}
    assigned_ids = [a.get("task_id") for a in assignments]
    mandatory = {t["task_id"] for t in tasks.values() if t["mandatory"]}
    if (not mandatory.issubset(set(map(str, assigned_ids)))
            or len(assigned_ids) != len(set(map(str, assigned_ids)))):
        errors.append("task bắt buộc thiếu/trùng")
    if plan.get("unassigned_tasks", []) != []:
        errors.append("draft không được có task chưa phân công")
    timelines = {n: [] for n in nurses}
    task_rows = {n: [] for n in nurses}
    loads = {n: 0 for n in nurses}
    nurse_breaks = {n: [] for n in nurses}
    task_times = {}
    resource_events = {key: [] for key in shift.get("equipment_capacity", {})}
    for row in assignments + breaks:
        nurse_id, start, end = row.get("nurse_id"), row.get("start"), row.get("end")
        if not isinstance(nurse_id, str) or nurse_id not in nurses or not interval(start, end, horizon):
            errors.append("ID/thời gian output không hợp lệ")
            continue
        nurse = nurses[nurse_id]
        if start < nurse["available_from"] or end > nurse["available_to"]:
            errors.append(nurse_id + ": ngoài availability")
        timelines[nurse_id].append((start, end))
        if "task_id" not in row:
            nurse_breaks[nurse_id].append((start, end))
            continue
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or task_id not in tasks:
            errors.append("task ID không tồn tại")
            continue
        task = tasks[task_id]
        if (not set(task["required_skill"]).issubset(nurse["skills"])
                or ("required_skill_level" in task
                    and nurse["qualification_level"] < task["required_skill_level"])):
            errors.append(task_id + ": sai kỹ năng")
        if patients[task["patient_id"]]["zone"] != nurse["home_zone"]:
            errors.append(task_id + ": ngoài zone cố định của nurse")
        if end - start != task["est_duration_min"]:
            errors.append(task_id + ": sai duration")
        if start < task["earliest_start"] or end > task["deadline"]:
            errors.append(task_id + ": ngoài time window")
        loads[nurse_id] += end - start
        task_rows[nurse_id].append((start, end, task))
        task_times[task_id] = (start, end)
        for resource in task.get("equipment_required", []):
            resource_events[resource].extend([(start, 1), (end, -1)])
    for task_id, task in tasks.items():
        predecessor = task.get("precedence_task_id")
        if predecessor and predecessor in task_times and task_id in task_times:
            if task_times[predecessor][1] > task_times[task_id][0]:
                errors.append(task_id + ": vi phạm precedence")
    for resource, events in resource_events.items():
        active = 0
        # At equal timestamps releases precede acquisitions: intervals are [s, e).
        for _, delta in sorted(events):
            active += delta
            if active > shift["equipment_capacity"][resource]:
                errors.append(resource + ": vượt equipment_capacity")
                break
    overhead = 0
    for nurse_id, nurse in nurses.items():
        ordered = sorted(task_rows[nurse_id], key=lambda row: row[0])
        for previous, following in zip(ordered, ordered[1:]):
            if patients[previous[2]["patient_id"]]["room"] != patients[following[2]["patient_id"]]["room"]:
                travel = shift["room_switch_min"]
                if travel:
                    segment = (following[0] - travel, following[0])
                    timelines[nurse_id].append(segment)
                    if segment[0] < previous[1] or segment[0] < nurse["available_from"]:
                        errors.append(nurse_id + ": thiếu thời gian chuyển phòng")
                overhead += travel
                loads[nurse_id] += travel
        policy = shift["break_policy"]
        rests = nurse_breaks[nurse_id]
        if not (len(rests) == 1 and rests[0][1]-rests[0][0] == policy["duration_min"]
                and policy["window"][0] <= rests[0][0] < rests[0][1] <= policy["window"][1]):
            errors.append(nurse_id + ": nghỉ không đúng chính sách")
        ordered_intervals = sorted(timelines[nurse_id])
        if any(overlap(a, b) for a, b in zip(ordered_intervals, ordered_intervals[1:])):
            errors.append(nurse_id + ": task/travel/break chồng lịch")
        if loads[nurse_id] > nurse["max_capacity_min"]:
            errors.append(nurse_id + ": vượt capacity")
    for rule in shift["coverage_rules"]:
        for minute in range(rule["start"], rule["end"]):
            count = sum(n["available_from"] <= minute < n["available_to"]
                        and n["home_zone"] == rule["zone"]
                        and (rule["required_skill"] is None or rule["required_skill"] in n["skills"])
                        and not any(start <= minute < end for start, end in nurse_breaks[nid])
                        for nid, n in nurses.items())
            if count < rule["min_staff"]:
                errors.append("coverage thiếu tại phút %d" % minute)
                break
    utilization = [loads[nid] / n["max_capacity_min"] for nid, n in nurses.items()]
    mean = statistics.mean(utilization)
    metrics = {"workload_minutes": loads, "overhead_minutes": overhead,
               "utilization_cv": statistics.pstdev(utilization)/mean if mean else 0,
               "peak_utilization": max(utilization)}
    return {"valid": not errors, "violations": sorted(set(errors)), "metrics": metrics}


def draft_schedule(instance):
    """Heuristic CP2: nghỉ luân phiên rồi gán việc; không chứng minh tối ưu/bất khả thi."""
    shift = instance["shift"]
    nurses = instance["nurses"]
    policy = shift["break_policy"]
    rests = [{"nurse_id":n["nurse_id"],
              "start":policy["window"][0]+i*policy["duration_min"],
              "end":policy["window"][0]+(i+1)*policy["duration_min"]}
             for i,n in enumerate(nurses)]
    if any(b["end"] > policy["window"][1] for b in rests):
        return {"status":"unknown", "warnings":["Heuristic chưa bố trí được nghỉ; cần solver/review."]}
    patients = {p["patient_id"]:p for p in instance["patients"]}
    tasks = sorted(instance["tasks"],key=lambda t:(t["earliest_start"],t["deadline"],
                                                 patients[t["patient_id"]]["room"],-t["est_duration_min"]))
    assignments, last, loads = [], {}, {n["nurse_id"]:0 for n in nurses}
    multiple_rooms = len({p["room"] for p in patients.values()}) > 1
    for task in tasks:
        patient = patients[task["patient_id"]]
        eligible = [n for n in nurses if set(task["required_skill"]).issubset(n["skills"])
                    and n["home_zone"] == patient["zone"]
                    and ("required_skill_level" not in task
                         or n["qualification_level"] >= task["required_skill_level"])]
        if not eligible and task["mandatory"]:
            return {"status":"infeasible", "warnings":[task["task_id"]+": không có nurse đủ skill/zone/level."]}
        options = []
        for n in eligible:
            nid = n["nurse_id"]
            previous_end, previous_room = last.get(nid,(n["available_from"],None))
            travel = shift["room_switch_min"] if previous_room and previous_room != patient["room"] else 0
            if loads[nid]+travel+task["est_duration_min"] > n["max_capacity_min"]:
                continue
            for start in range(max(task["earliest_start"], previous_end+travel, n["available_from"]+travel),
                               min(task["deadline"],n["available_to"])-task["est_duration_min"]+1):
                end = start+task["est_duration_min"]
                rest = next(b for b in rests if b["nurse_id"]==nid)
                if overlap((start-travel,end),(rest["start"],rest["end"])):
                    continue
                affinity = 30 if multiple_rooms and previous_room != patient["room"] else 0
                options.append((loads[nid]+affinity, start, nid, end, travel))
                break
        if not options:
            return {"status":"unknown", "warnings":[task["task_id"]+": heuristic chưa tìm được chỗ; không kết luận infeasible."]}
        _,start,nid,end,travel = min(options)
        assignments.append({"task_id":task["task_id"],"nurse_id":nid,"start":start,"end":end})
        loads[nid] += travel+task["est_duration_min"]
        last[nid] = (end,patient["room"])
    return {"status":"draft", "approval_required":True, "assignments":assignments,
            "breaks":rests, "unassigned_tasks":[], "warnings":[]}
