"""Integration L3 với các module đang có trên develop, không sửa code của module khác.

Mức kiểm: L3 → kiểm đủ (planning.input_issues) → solve_allocation → validate_plan.
solve_allocation gọi L2 CP-SAT; mọi draft được validator độc lập kiểm lại.
Đây KHÔNG phải test end-to-end NurseFlow: chưa đi qua answer()/LLM của L1.
"""
import copy
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
from planning import input_issues, validate_plan
from tools import solve_allocation
from workload import DurationNeedInfo, estimate_duration

BUNDLE = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))


def load_l4():
    """Nạp L4 (codebase/baseline.py) nếu đã merge; L4_BASELINE_PATH cho phép trỏ tới bản đọc thử."""
    path = Path(os.environ.get("L4_BASELINE_PATH", ROOT / "codebase" / "baseline.py"))
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("l4_baseline", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class L3ToSolverIntegrationTests(unittest.TestCase):
    def test_l3_output_passes_full_check_cp_sat_and_validator(self):
        for case in BUNDLE["cases"]:
            with self.subTest(case=case["id"]):
                original = copy.deepcopy(case["l3_input"])
                self.assertEqual(input_issues(original, require_duration=False), [])
                instance = estimate_duration(original)
                self.assertEqual(original, case["l3_input"])
                self.assertEqual(instance, case["instance"])
                self.assertEqual(input_issues(instance), [])
                plan = solve_allocation(instance)
                self.assertEqual(plan["status"], "draft", plan.get("warnings"))
                self.assertEqual(plan["method"], "cp_sat")
                result = validate_plan(instance, plan)
                self.assertTrue(result["valid"], result["violations"])
                durations = {t["task_id"]: t["est_duration_min"] for t in instance["tasks"]}
                for row in plan["assignments"]:
                    self.assertEqual(row["end"] - row["start"], durations[row["task_id"]])

    def test_need_info_stops_before_solver(self):
        data = copy.deepcopy(BUNDLE["cases"][1]["l3_input"])
        data["tasks"][1]["task_type"] = "toileting"
        with self.assertRaises(DurationNeedInfo) as ctx:
            estimate_duration(data)
        self.assertTrue(any("staff_required" in m for m in ctx.exception.missing_fields))
        self.assertIsNone(ctx.exception.report["instance"])


@unittest.skipIf(load_l4() is None, "L4 (codebase/baseline.py) chưa có trên nhánh này")
class L3ToL4IntegrationTests(unittest.TestCase):
    def test_l4_baseline_runs_on_l3_output_and_is_validated(self):
        l4 = load_l4()
        for case in BUNDLE["cases"]:
            with self.subTest(case=case["id"]):
                instance = estimate_duration(copy.deepcopy(case["l3_input"]))
                plan = l4.baseline_allocate(instance)
                self.assertIn(plan["status"], {"draft", "unknown", "infeasible"})
                if plan["status"] == "draft":
                    self.assertTrue(validate_plan(instance, plan)["valid"])


if __name__ == "__main__":
    unittest.main()
