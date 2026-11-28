"""Input boundary for L3 staging and explicit CP3 constraints."""
import copy
import unittest

from test_planning import sample
from planning import input_issues


class InputStageTests(unittest.TestCase):
    def test_blank_skill_and_coverage_fields_are_missing_information(self):
        for change in ["skills", "coverage_skill", "coverage_zone", "nurse_zone", "task_type", "task_id", "patient_id"]:
            instance, _ = sample()
            if change == "skills":
                for nurse in instance["nurses"]:
                    nurse["skills"] = [" "]
                instance["tasks"][0]["required_skill"] = [" "]
                instance["shift"]["coverage_rules"][0]["required_skill"] = " "
            elif change.startswith("coverage"):
                key = "required_skill" if change == "coverage_skill" else "zone"
                instance["shift"]["coverage_rules"][0][key] = ""
            elif change == "nurse_zone":
                instance["nurses"][0]["home_zone"] = " "
            elif change == "patient_id":
                instance["patients"][0]["patient_id"] = " "
                instance["tasks"][0]["patient_id"] = " "
            else:
                instance["tasks"][0][change] = " "
            with self.subTest(change=change):
                self.assertTrue(input_issues(instance))
                self.assertTrue(input_issues(instance, require_duration=False))

    def test_midshift_state_is_not_treated_as_a_fresh_task(self):
        for field, value in [("status", "completed"), ("status", "in_progress"), ("locked", True)]:
            instance, _ = sample()
            instance["tasks"][0][field] = value
            with self.subTest(field=field, value=value):
                self.assertTrue(input_issues(instance))

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

    def test_l3_staff_count_cannot_silently_become_single_staff(self):
        for count in [None, True, 0, 2, 1.5, "1"]:
            instance, _ = sample()
            instance["tasks"][0]["staff_required"] = count
            with self.subTest(count=count):
                self.assertTrue(input_issues(instance))
        instance["tasks"][0]["staff_required"] = 1
        self.assertFalse(input_issues(instance))

    def test_multiple_break_blocks_are_not_silently_ignored(self):
        instance, _ = sample()
        instance["shift"]["break_policy"]["blocks"] = [{"duration_min": 15}, {"duration_min": 30}]
        self.assertTrue(input_issues(instance))


if __name__ == "__main__":
    unittest.main()
