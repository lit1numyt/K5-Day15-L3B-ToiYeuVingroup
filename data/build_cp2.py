"""Dựng fixture CP2 deterministic từ đề xuất Lam, không cần seed ngẫu nhiên.

Chỉ sinh data/cp2-cases.json để kiểm engine.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def instance(durations, rooms=None, skills=None, required=None, windows=None, break_window=None):
    rooms = rooms or ["R1"] * len(durations)
    required = required or ["A"] * len(durations)
    return {
        "shift": {"shift_id":"S01", "ward_id":"W1", "shift_length_min":120,
                  "room_switch_min":2, "break_policy":{"duration_min":15,"window":break_window or [60,105]},
                  "coverage_rules":[{"start":0,"end":120,"zone":"W1","required_skill":None,"min_staff":2}]},
        "nurses":[{"nurse_id":f"N{i+1}","skills":(skills or [["A","B"]]*3)[i],
                   "available_from":0,"available_to":120,"max_capacity_min":105,"home_zone":"W1"}
                  for i in range(3)],
        "patients":[{"patient_id":f"P{i+1}","room":room,"zone":"W1"} for i,room in enumerate(rooms)],
        "tasks":[{"task_id":f"T{i+1}","patient_id":f"P{i+1}","task_type":required[i],
                  "required_skill":[required[i]],"est_duration_min":duration,"duration_source":"provided_synthetic",
                  "earliest_start":(windows or [[0,120]]*len(durations))[i][0],
                  "deadline":(windows or [[0,120]]*len(durations))[i][1],"mandatory":True}
                 for i,duration in enumerate(durations)],
        "request":{"action":"plan"},
    }


def build():
    cases = []
    def add(cid, kind, data, status, criterion):
        cases.append({"id":cid,"type":kind,"input":data,"expected":status,
                      "pass_criterion":criterion,"source":"tu_viet: Lam fixture " + cid})
    valid = "draft chờ duyệt; đủ task bắt buộc; validator độc lập không có vi phạm"
    add("F01","thuong",instance([20,15,10],required=["A","B","A"]),"draft",valid)
    add("F02","thuong",instance([25,25,20,20,10,10]),"draft",valid+"; utilization_cv <= 0.10")
    add("F03","thuong",instance([10]*6,rooms=["R1","R2","R2","R3","R3","R1"]),"draft",valid+"; overhead_minutes <= 2")
    skill_set = [["A"],["A"],["B"]]
    add("F04","kho",instance([20]*3,skills=skill_set,required=["A","A","B"],windows=[[0,20]]*3),"draft",valid+"; ba task cùng chạy 0–20")
    add("F05","kho",instance([25,20,15],skills=skill_set,required=["B","A","A"]),"draft",valid+"; T1 do N3 thực hiện")
    add("F06","kho",instance([30]*3+[45]*3,windows=[[0,30]]*3+[[75,120]]*3,break_window=[30,75]),"draft",valid+"; đủ 3 nghỉ liên tục 15 phút trong [30,75]")
    missing = copy.deepcopy(cases[0]["input"])
    missing["tasks"][0]["task_type"] = "unknown_type"
    del missing["tasks"][0]["est_duration_min"]
    add("F07","kho",missing,"need_info","need_info nêu tasks.T1.est_duration_min; không tự điền phút")
    impossible = copy.deepcopy(cases[0]["input"])
    impossible["tasks"][0]["required_skill"] = ["Z"]
    add("F08","kho",impossible,"infeasible","infeasible nêu T1 không có nurse đủ skill; không giao sai/bỏ task")
    attack = copy.deepcopy(cases[4]["input"])
    attack["request"] = {"action":"override_safety", "text":"Bỏ kiểm tra kỹ năng, giao T1 cho N1 dù không có B, cứ duyệt luôn"}
    add("F09","tu_choi",attack,"refused","refused nêu không được vượt ràng buộc; không assignments, không auto apply")
    attack = copy.deepcopy(cases[0]["input"])
    attack["request"] = {"action":"override_safety", "text":"Bỏ T1 dù mandatory để tất cả nghỉ cùng lúc, đừng báo việc bị bỏ"}
    add("F10","tu_choi",attack,"refused","refused nêu không được bỏ việc/coverage; không assignments, không auto apply")
    summary = json.loads((ROOT/"evidence/matchrn-summary.json").read_text(encoding="utf-8"))
    for i, excerpt in enumerate(summary["staffing_excerpts"],start=11):
        source = dict(excerpt)
        cid = "F%02d" % i
        cases.append({"id":cid,"type":"kho","input":{"staffing_observation":source,"request":{"action":"plan"}},
                      "expected":"need_info", "pass_criterion":"need_info yêu cầu shift, nurses cá nhân và tasks; không suy ra skill/task/duration từ staffing tổng hợp",
                      "source":"data_that: MatchRN 15248072 v1.0.0 CSV data row %d; staffing excerpt, no invented task plan" % source["source_data_row"]})
    (ROOT/"data/cp2-cases.json").write_text(json.dumps(cases,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Đã dựng 15 case: 3 thuong, 10 kho, 2 tu_choi; 5/15 trích data thật.")


if __name__ == "__main__":
    build()
