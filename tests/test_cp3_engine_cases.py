"""Technical acceptance cases have declared assumptions and independent outcomes."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from test_planning import sample  # establishes the existing module path
from planning import input_issues, validate_plan
from cp_sat_engine import solve_allocation

ROOT = Path(__file__).resolve().parents[1]


class AcceptanceCases(unittest.TestCase):
    def test_generated_cases_reproduce_and_meet_hand_calculated_statuses(self):
        path = ROOT / "scripts/data/build_cp3_engine_cases.py"
        self.assertTrue(path.exists(), "Missing reproducible engine cases")
        spec = importlib.util.spec_from_file_location("cp3_cases", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "cases.json"
            module.build_cases(ROOT, output)
            self.assertEqual(output.read_bytes(), (ROOT / "data/cp3-engine-cases.json").read_bytes())
            bundle = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(bundle["data_kind"], "synthetic")
        expected = {"C01": "draft", "C02": "draft", "C03": "draft", "C04": "infeasible",
                    "C05": "draft", "C06": "infeasible", "C07": "draft", "C08": "infeasible"}
        self.assertEqual({c["id"] for c in bundle["cases"]}, set(expected))
        for case in bundle["cases"]:
            with self.subTest(case=case["id"]):
                self.assertFalse(input_issues(case["instance"]))
                result = solve_allocation(case["instance"])
                self.assertEqual(result["status"], expected[case["id"]], result)
                if result["status"] == "draft":
                    self.assertTrue(validate_plan(case["instance"], result)["valid"])
                    if case["id"] == "C02":
                        rows = {a["task_id"]: a for a in result["assignments"]}
                        self.assertGreaterEqual(rows["T3"]["start"], 105)
                        self.assertGreaterEqual(rows["T4"]["start"], 110)
                    if case["id"] == "C07":
                        task = next(a for a in result["assignments"] if a["task_id"] == "T2")
                        self.assertEqual((task["start"], task["end"]), (77, 97))


if __name__ == "__main__":
    unittest.main()
