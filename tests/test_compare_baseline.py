"""Comparison revalidates plans and distinguishes policy failure from no solution."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from test_planning import sample
from baseline import baseline_allocate
from planning import validate_plan

ROOT = Path(__file__).resolve().parents[1]


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "comparison", ROOT / "scripts/benchmark/compare_baseline.py"
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_metrics_are_recomputed(self):
        instance, plan = sample()
        plan["metrics"] = {"utilization_cv": -1, "peak_utilization": -1, "overhead_minutes": -999}
        out = self.module.evaluate_plan(instance, plan)
        self.assertTrue(out["valid"])
        self.assertEqual(out["metrics"]["workload_minutes"], {"N1": 20, "N2": 0, "N3": 0})
        self.assertEqual(out["metrics"]["overhead_minutes"], 0)
        self.assertAlmostEqual(out["metrics"]["peak_utilization"], 20 / 105)

    def test_invalid_draft_is_not_scored(self):
        instance, plan = sample()
        plan.update(assignments=[], breaks=[], metrics={"overhead_minutes": -999})
        out = self.module.evaluate_plan(instance, plan)
        self.assertFalse(out["valid"])
        self.assertTrue(out["violations"])
        self.assertIsNone(out["metrics"])

    def test_baseline_continuity_failure_is_not_global_infeasible(self):
        data = json.loads((ROOT / "data/cp3-engine-cases.json").read_text(encoding="utf-8"))
        instance = next(c["instance"] for c in data["cases"] if c["id"] == "C05")
        for balance in ("count", "weight"):
            out = baseline_allocate(instance, balance)
            self.assertEqual(out["status"], "unknown", out)
            self.assertFalse(out.get("assignments"))

    def test_baseline_direct_skill_gap_still_has_infeasibility_evidence(self):
        instance, _ = sample()
        instance["tasks"][0]["required_skill"] = ["Z"]
        for balance in ("count", "weight"):
            self.assertEqual(baseline_allocate(instance, balance)["status"], "infeasible")

    def test_runner_copies_inputs_and_keeps_failed_results(self):
        instance, plan = sample()
        case = {"id": "PRIVATE", "instance": instance}
        original = copy.deepcopy(instance)

        def mutating_allocator(data):
            data["tasks"].clear()
            return plan

        records = self.module.compare_cases([case], {
            "candidate": mutating_allocator,
            "unavailable": lambda data: {"status": "unknown", "warnings": ["not found"]},
        })
        self.assertEqual(instance, original)
        self.assertEqual(len(records), 2)
        self.assertTrue(records[0]["valid"])
        self.assertEqual(records[1]["status"], "unknown")
        self.assertIsNone(records[1]["metrics"])

    def test_comparison_writes_new_runs_without_overwriting(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            first = self.module.save_comparison([], Path(folder), {})
            before = first.read_bytes()
            second = self.module.save_comparison([], Path(folder), {})
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), before)
            self.assertTrue(first.with_suffix(".csv").exists())

    def test_cli_keeps_both_khoa_baselines_and_real_l2(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/benchmark/compare_baseline.py"),
                 "--output-dir", folder], check=True, capture_output=True, text=True,
            )
            run = json.loads((Path(folder) / "l2-comparison-1.json").read_text())
            self.assertEqual(len(run["records"]), 44)
            self.assertEqual({r["allocator"] for r in run["records"]}, {
                "l4_patient_count", "l4_patient_weight", "cp_sat", "cp2_heuristic",
            })
            for record in run["records"]:
                if record["allocator"] == "cp_sat":
                    self.assertEqual(record["output"]["method"], "cp_sat")


if __name__ == "__main__":
    unittest.main()
