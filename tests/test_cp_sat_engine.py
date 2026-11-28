"""Exercise the real CP-SAT engine with small independently checkable schedules."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from test_planning import sample
from planning import draft_schedule, validate_plan
from cp_sat_engine import solve_allocation


class SolverTests(unittest.TestCase):
    def test_registered_tool_runs_the_real_cp_sat_backend(self):
        from tools import solve_allocation as tool_solve
        instance, _ = sample()
        result = tool_solve(instance)
        self.assertEqual(result.get("method"), "cp_sat")
        self.assertTrue(result["validation"]["valid"])

    def checked(self, instance):
        before = copy.deepcopy(instance)
        plan = solve_allocation(instance)
        self.assertEqual(instance, before, "Solver mutated its input")
        self.assertEqual(plan["status"], "draft", plan)
        self.assertTrue(plan["approval_required"])
        self.assertEqual(plan["method"], "cp_sat")
        self.assertIn(plan["solver"]["status"], ["FEASIBLE", "OPTIMAL"])
        self.assertTrue(validate_plan(instance, plan)["valid"], plan)
        return plan

    def test_shared_cases_and_cp2_quality_anchors(self):
        root = Path(__file__).resolve().parents[1]
        shared = json.loads((root / "data/preliminary/instances.json").read_text(encoding="utf-8"))
        for case in shared["cases"]:
            with self.subTest(case=case["id"]):
                self.checked(case["instance"])
        old = json.loads((root / "data/cp2-cases.json").read_text(encoding="utf-8"))
        for case in old:
            if case["expected"] == "draft":
                with self.subTest(case=case["id"]):
                    plan = self.checked(case["input"])
                    if case["id"] == "F02":
                        self.assertLessEqual(plan["metrics"]["utilization_cv"], 0.10)
                    if case["id"] == "F03":
                        self.assertLessEqual(plan["metrics"]["overhead_minutes"], 2)

    def test_break_solver_can_use_parallel_breaks_when_coverage_allows(self):
        instance, _ = sample()
        instance["shift"]["break_policy"]["window"] = [60, 90]
        instance["shift"]["coverage_rules"][0]["min_staff"] = 1
        self.assertEqual(draft_schedule(instance)["status"], "unknown")
        self.checked(instance)

    def test_precedence_and_one_shared_device_are_respected(self):
        instance, _ = sample()
        instance["shift"]["equipment_capacity"] = {"E1": 1}
        first = instance["tasks"][0]
        first["equipment_required"] = ["E1"]
        second = dict(first, task_id="T2", precedence_task_id="T1")
        instance["tasks"].append(second)
        plan = self.checked(instance)
        rows = {a["task_id"]: a for a in plan["assignments"]}
        self.assertLessEqual(rows["T1"]["end"], rows["T2"]["start"])

    def test_same_patient_can_have_different_qualified_nurses(self):
        instance, _ = sample()
        instance["nurses"] = instance["nurses"][:2]
        instance["shift"]["coverage_rules"][0]["min_staff"] = 1
        instance["nurses"][0]["skills"] = ["A"]
        instance["nurses"][1]["skills"] = ["B"]
        instance["tasks"].append(dict(instance["tasks"][0], task_id="T2", required_skill=["B"]))
        plan = self.checked(instance)
        self.assertEqual({a["nurse_id"] for a in plan["assignments"]}, {"N1", "N2"})

    def test_no_qualified_nurse_is_infeasible(self):
        instance, _ = sample()
        instance["tasks"][0]["required_skill"] = ["MISSING"]
        plan = solve_allocation(instance)
        self.assertEqual(plan["status"], "infeasible")
        self.assertFalse(plan.get("assignments"))
        self.assertTrue(plan["approval_required"])

    def test_valid_input_with_impossible_window_is_proven_infeasible(self):
        instance, _ = sample()
        instance["tasks"][0]["deadline"] = 10  # 20 minutes cannot finish by 10.
        plan = solve_allocation(instance)
        self.assertEqual(plan["status"], "infeasible", plan)
        self.assertEqual(plan["solver"]["status"], "INFEASIBLE")

    def test_missing_data_needs_info_and_never_estimates(self):
        instance, _ = sample()
        del instance["tasks"][0]["est_duration_min"]
        plan = solve_allocation(instance)
        self.assertEqual(plan["status"], "need_info")
        self.assertIn("est_duration_min", " ".join(plan["missing_fields"]))

    def test_capacity_proportion_not_equal_raw_minutes(self):
        instance, _ = sample()
        instance["nurses"] = instance["nurses"][:2]
        instance["shift"]["coverage_rules"][0]["min_staff"] = 1
        instance["nurses"][0]["max_capacity_min"] = 30
        instance["nurses"][1]["max_capacity_min"] = 90
        instance["tasks"] = [dict(instance["tasks"][0], task_id=f"T{i}", est_duration_min=10)
                             for i in range(6)]
        plan = self.checked(instance)
        self.assertEqual(plan["metrics"]["workload_minutes"], {"N1": 10, "N2": 50})

    def test_given_minutes_are_not_multiplied_by_taxonomy(self):
        instance, _ = sample()
        instance["patients"][0].update(tier=3, workload_weight=999)
        plan = self.checked(instance)
        row = plan["assignments"][0]
        self.assertEqual(row["end"] - row["start"], 20)

    def test_zero_search_budget_is_unknown_not_infeasible(self):
        instance, _ = sample()
        with patch("cp_sat_engine.TIME_LIMIT_SECONDS", 0):
            plan = solve_allocation(instance)
        self.assertEqual(plan["status"], "unknown", plan)
        self.assertFalse(plan.get("assignments"))

    def test_invalid_solver_model_surfaces_as_technical_error(self):
        from ortools.sat.python import cp_model
        instance, _ = sample()
        with patch.object(cp_model.CpSolver, "solve", return_value=cp_model.MODEL_INVALID):
            with self.assertRaises(RuntimeError):
                solve_allocation(instance)


if __name__ == "__main__":
    unittest.main()
