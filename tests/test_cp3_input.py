"""Input boundary for L3 staging and explicit CP3 constraints."""
import copy
import unittest

from test_planning import sample
from planning import input_issues


class InputStageTests(unittest.TestCase):
    def test_missing_duration_is_allowed_only_before_l3(self):
        instance, _ = sample()
        del instance["tasks"][0]["est_duration_min"]
        self.assertFalse(input_issues(instance, require_duration=False))
        self.assertTrue(input_issues(instance))
        instance["tasks"][0]["required_skill"] = []
        self.assertTrue(input_issues(instance, require_duration=False))

    def test_invalid_given_duration_still_fails_before_l3(self):
        for value in [None, 0, -1, True, 2.5, "10"]:
            instance, _ = sample()
            instance["tasks"][0]["est_duration_min"] = value
            with self.subTest(value=value):
                self.assertTrue(input_issues(instance, require_duration=False))

    def test_predecessor_exists_and_graph_is_acyclic(self):
        instance, _ = sample()
        second = dict(instance["tasks"][0], task_id="T2", precedence_task_id="T1")
        instance["tasks"].append(second)
        self.assertFalse(input_issues(instance))
        for predecessor in ["MISSING", "T2", []]:
            instance["tasks"][1]["precedence_task_id"] = predecessor
            with self.subTest(predecessor=predecessor):
                self.assertTrue(input_issues(instance))
        instance["tasks"][1]["precedence_task_id"] = "T1"
        instance["tasks"][0]["precedence_task_id"] = "T2"
        self.assertTrue(input_issues(instance))

    def test_equipment_requires_explicit_capacity(self):
        instance, _ = sample()
        instance["tasks"][0]["equipment_required"] = ["E1"]
        self.assertTrue(input_issues(instance))
        instance["shift"]["equipment_capacity"] = {"E1": 1}
        self.assertFalse(input_issues(instance))
        for value in [0, True, -1, 1.5]:
            instance["shift"]["equipment_capacity"]["E1"] = value
            with self.subTest(value=value):
                self.assertTrue(input_issues(instance))

    def test_invalid_equipment_shape_is_rejected(self):
        original, _ = sample()
        original["shift"]["equipment_capacity"] = {"E1": 1}
        for value in ["E1", ["E1", "E1"], [None], ["MISSING"]]:
            instance = copy.deepcopy(original)
            instance["tasks"][0]["equipment_required"] = value
            with self.subTest(value=value):
                self.assertTrue(input_issues(instance))

    def test_unsupported_synchronization_is_not_ignored(self):
        instance, _ = sample()
        instance["tasks"][0]["synchronization"] = {"staff_count": 2}
        self.assertTrue(input_issues(instance))


if __name__ == "__main__":
    unittest.main()
