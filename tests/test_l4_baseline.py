"""Test L4 (taxonomy + baseline) — stdlib, không cần pandas."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

from baseline import baseline_allocate, classify_patient  # noqa: E402
from planning import validate_plan  # noqa: E402

BUNDLE = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
CASES = {c["id"]: c["instance"] for c in BUNDLE["cases"]}


class ClassifyPatient(unittest.TestCase):
    def test_tiers_increase_with_acuity_and_adl(self):
        low = classify_patient({"acuity_score": 1, "adl_dependency": 1, "care_category": "medical"})
        high = classify_patient({"acuity_score": 5, "adl_dependency": 4,
                                 "isolation_precaution": True, "care_category": "medical"})
        self.assertEqual(low["tier"], 1)
        self.assertEqual(high["tier"], 3)
        self.assertGreater(high["workload_weight"], low["workload_weight"])

    def test_isolation_adds_weight(self):
        base = classify_patient({"acuity_score": 3, "adl_dependency": 2})
        iso = classify_patient({"acuity_score": 3, "adl_dependency": 2, "isolation_precaution": True})
        self.assertEqual(iso["workload_weight"], base["workload_weight"] + 1)

    def test_missing_attrs_ask_not_guess(self):
        out = classify_patient({"care_category": "medical"})
        self.assertIsNone(out["tier"])
        self.assertIn("acuity_score", out["need_info"])

    def test_weight_is_not_claimed_as_minutes(self):
        # Trọng số là tương đối (McGill ordinal), không phải phút.
        self.assertIn("không phải phút", classify_patient(
            {"acuity_score": 2, "adl_dependency": 1})["basis"])


class BaselineAllocate(unittest.TestCase):
    def test_preliminary_cases_are_valid_drafts(self):
        for cid, instance in CASES.items():
            plan = baseline_allocate(instance)
            self.assertEqual(plan["status"], "draft", f"{cid}: {plan.get('warnings')}")
            self.assertTrue(plan["approval_required"])
            self.assertTrue(validate_plan(instance, plan)["valid"], cid)

    def test_continuity_one_nurse_per_patient(self):
        instance = CASES["P01"]
        plan = baseline_allocate(instance)
        task_patient = {t["task_id"]: t["patient_id"] for t in instance["tasks"]}
        patient_nurses = {}
        for a in plan["assignments"]:
            patient_nurses.setdefault(task_patient[a["task_id"]], set()).add(a["nurse_id"])
        for pid, nurses in patient_nurses.items():
            self.assertEqual(len(nurses), 1, f"{pid} bị chia cho nhiều điều dưỡng")

    def test_needs_info_on_empty_input(self):
        self.assertEqual(baseline_allocate({})["status"], "need_info")

    def test_draft_only_never_auto_applies(self):
        plan = baseline_allocate(CASES["P03"])
        self.assertTrue(plan["approval_required"])


if __name__ == "__main__":
    unittest.main()
