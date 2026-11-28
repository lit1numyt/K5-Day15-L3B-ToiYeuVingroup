"""Hand-calculated schedules for the CP3 additions to the shared oracle."""
import unittest

from test_planning import sample
from planning import validate_plan


class ExtendedOracleTests(unittest.TestCase):
    def two_tasks(self):
        instance, plan = sample()
        instance["tasks"].append(dict(instance["tasks"][0], task_id="T2"))
        plan["assignments"].append({"task_id": "T2", "nurse_id": "N2", "start": 0, "end": 20})
        return instance, plan

    def test_precedence_is_checked_across_nurses(self):
        instance, plan = self.two_tasks()
        instance["tasks"][1]["precedence_task_id"] = "T1"
        self.assertFalse(validate_plan(instance, plan)["valid"])
        plan["assignments"][1].update(start=20, end=40)
        self.assertTrue(validate_plan(instance, plan)["valid"])
        plan["assignments"][0].update(start=20, end=40)
        plan["assignments"][1].update(start=0, end=20)
        self.assertFalse(validate_plan(instance, plan)["valid"])

    def test_equipment_capacity_and_half_open_boundaries(self):
        instance, plan = self.two_tasks()
        instance["shift"]["equipment_capacity"] = {"E1": 1}
        for task in instance["tasks"]:
            task["equipment_required"] = ["E1"]
        self.assertFalse(validate_plan(instance, plan)["valid"])
        instance["shift"]["equipment_capacity"]["E1"] = 2
        self.assertTrue(validate_plan(instance, plan)["valid"])
        instance["shift"]["equipment_capacity"]["E1"] = 1
        plan["assignments"][1].update(start=20, end=40)
        self.assertTrue(validate_plan(instance, plan)["valid"])

    def test_travel_cannot_overlap_recovery_even_with_idle_time(self):
        instance, plan = self.two_tasks()
        instance["patients"].append({"patient_id": "P2", "room": "R2", "zone": "W1"})
        instance["tasks"][1]["patient_id"] = "P2"
        plan["assignments"][1].update(nurse_id="N1", start=75, end=95)
        self.assertFalse(validate_plan(instance, plan)["valid"])
        plan["assignments"][1].update(start=77, end=97)
        result = validate_plan(instance, plan)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["metrics"]["workload_minutes"]["N1"], 42)
        self.assertEqual(result["metrics"]["overhead_minutes"], 2)

    def test_taxonomy_does_not_change_task_minutes(self):
        instance, plan = sample()
        expected = validate_plan(instance, plan)["metrics"]
        instance["patients"][0].update(tier=3, workload_weight=999)
        self.assertEqual(validate_plan(instance, plan)["metrics"], expected)

    def test_contradictory_unassigned_list_is_invalid(self):
        instance, plan = sample()
        plan["unassigned_tasks"] = ["T1"]
        self.assertFalse(validate_plan(instance, plan)["valid"])


if __name__ == "__main__":
    unittest.main()
