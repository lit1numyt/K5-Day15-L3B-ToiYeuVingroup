"""Chấm kỹ thuật CP2 từ output thật của luồng hiện tại; không phải lượt AI CP3."""
import json
import os
import sys
from pathlib import Path

os.environ["MODEL_PROVIDER"] = "fake"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
from agent import answer
from planning import validate_plan


def grade(row, output):
    issues = []
    if output.get("status") != row["expected"]:
        issues.append("status khác expected")
    if output.get("approval_required") is not True:
        issues.append("thiếu chốt người duyệt")
    instance = row["input"]
    if output.get("status") == "draft":
        checked = validate_plan(instance, output)
        issues.extend(checked["violations"])
        if checked["valid"]:
            if row["id"] == "F02" and checked["metrics"]["utilization_cv"] > 0.10:
                issues.append("CV vượt 0.10")
            if row["id"] == "F03" and checked["metrics"]["overhead_minutes"] > 2:
                issues.append("overhead vượt 2")
    elif output.get("assignments"):
        issues.append("trạng thái không draft nhưng vẫn giao việc")
    if output.get("status") == "need_info":
        missing = " ".join(output.get("missing_fields", []))
        required = ["tasks.T1.est_duration_min"] if row["id"] == "F07" else ["shift", "nurses", "tasks"]
        if any(field not in missing for field in required):
            issues.append("chưa chỉ rõ dữ liệu thiếu")
    if row["id"] == "F08" and "T1" not in " ".join(output.get("warnings", [])):
        issues.append("chưa nêu task thiếu skill")
    if row["type"] == "tu_choi" and not output.get("warnings"):
        issues.append("thiếu lý do từ chối")
    return issues


def main():
    rows = json.loads((ROOT / "data/cp2-cases.json").read_text(encoding="utf-8"))
    records = []
    for row in rows:
        result = json.loads(answer(json.dumps(row["input"], ensure_ascii=False))["output"])
        issues = grade(row, result)
        records.append({"id": row["id"], "pass": int(not issues), "issues": issues, "output": result})
    path = ROOT / "eval/cp2-review.json"
    path.write_text(json.dumps({"stage": "CP2", "method": "Kiểm kỹ thuật trên fixture của engine",
                                "model_provider": "fake", "records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    passed = sum(r["pass"] for r in records)
    print("CP2 kỹ thuật: %d/%d; output/lý do: eval/cp2-review.json" % (passed, len(records)))
    print("Chưa phải run-N AI thật; không dùng tỷ lệ này cho chi phí/task thành công CP4.")
    for record in records:
        print(record["id"], "PASS" if record["pass"] else "FAIL", "; ".join(record["issues"]))
    return int(passed != len(records))


if __name__ == "__main__":
    sys.exit(main())
