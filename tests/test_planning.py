"""Kiểm ràng buộc bằng lịch tính tay; không dùng solver sinh expected."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))
from planning import input_issues, validate_plan


def sample():
    instance = {
        "shift": {"shift_id": "S1", "ward_id": "W1", "shift_length_min": 120,
                  "break_policy": {"duration_min": 15, "window": [60, 105]},
                  "room_switch_min": 2,
                  "coverage_rules": [{"start": 0, "end": 120, "zone": "W1",
                                      "required_skill": None, "min_staff": 2}]},
        "nurses": [{"nurse_id": f"N{i}", "skills": ["A"], "home_zone": "W1",
                    "available_from": 0, "available_to": 120, "max_capacity_min": 105}
                   for i in range(1, 4)],
        "patients": [{"patient_id": "P1", "room": "R1", "zone": "W1"}],
        "tasks": [{"task_id": "T1", "patient_id": "P1", "task_type": "A",
                   "required_skill": ["A"], "est_duration_min": 20,
                   "earliest_start": 0, "deadline": 120, "mandatory": True}],
    }
    plan = {"status": "draft", "approval_required": True,
            "assignments": [{"task_id": "T1", "nurse_id": "N1", "start": 0, "end": 20}],
            "breaks": [{"nurse_id": f"N{i+1}", "start": 60+i*15, "end": 75+i*15}
                       for i in range(3)]}
    return instance, plan


class PlanTests(unittest.TestCase):
    def test_valid_plan_and_recomputed_load(self):
        instance, plan = sample()
        plan["metrics"] = {"overhead_minutes": -999}
        result = validate_plan(instance, plan)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["metrics"]["workload_minutes"], {"N1": 20, "N2": 0, "N3": 0})
        self.assertEqual(result["metrics"]["overhead_minutes"], 0)

    def test_missing_duration_is_input_issue(self):
        instance, _ = sample()
        del instance["tasks"][0]["est_duration_min"]
        self.assertTrue(input_issues(instance))

    def test_malformed_input_does_not_crash(self):
        for instance in [None, [], {"shift": []}, {"nurses": "N1"}]:
            with self.subTest(instance=instance):
                self.assertTrue(input_issues(instance))

    def test_unhashable_foreign_id_and_missing_task_type_need_info(self):
        for field, value in [("patient_id", []), ("task_type", None)]:
            instance, _ = sample()
            instance["tasks"][0][field] = value
            with self.subTest(field=field):
                self.assertTrue(input_issues(instance))

    def test_enforces_qualification_level_when_provided(self):
        instance, plan = sample()
        instance["tasks"][0]["required_skill_level"] = 2
        for nurse in instance["nurses"]:
            nurse["qualification_level"] = 1
        self.assertFalse(validate_plan(instance, plan)["valid"])
        instance["nurses"][0]["qualification_level"] = 2
        self.assertTrue(validate_plan(instance, plan)["valid"])

    def test_incomplete_coverage_rule_needs_clarification(self):
        instance, _ = sample()
        del instance["shift"]["coverage_rules"][0]["required_skill"]
        self.assertTrue(input_issues(instance))

    def test_mismatched_shift_or_ward_is_rejected(self):
        for entity, field in [("nurses", "shift_id"), ("patients", "ward_id")]:
            instance, _ = sample()
            instance[entity][0][field] = "OTHER"
            with self.subTest(entity=entity):
                self.assertTrue(input_issues(instance))
        for field in ("shift_id", "ward_id"):
            instance, _ = sample()
            del instance["shift"][field]
            with self.subTest(field=field):
                self.assertTrue(input_issues(instance))

    def test_task_hidden_in_breaks_is_not_valid(self):
        instance, plan = sample()
        plan["breaks"].append({"nurse_id":"N2", "task_id":"T1", "start":20, "end":40})
        self.assertFalse(validate_plan(instance, plan)["valid"])

    def test_assignment_without_task_id_cannot_masquerade_as_break(self):
        instance, plan = sample()
        plan["assignments"].append({"nurse_id":"N1", "start":30, "end":35})
        self.assertFalse(validate_plan(instance, plan)["valid"])

    def test_unsupported_hard_constraint_is_not_silently_ignored(self):
        for field, value in [("precedence_task_id","T2"), ("equipment_required",["E1"]),
                             ("synchronization",{"type":"simultaneous"})]:
            instance, _ = sample()
            instance["tasks"][0][field] = value
            with self.subTest(field=field):
                self.assertTrue(input_issues(instance))

    def test_rejects_mutations_of_valid_plan(self):
        mutations = {
            "omitted task": lambda x,p: p.update(assignments=[]),
            "duplicate task": lambda x,p: p["assignments"].append(copy.deepcopy(p["assignments"][0])),
            "wrong skill": lambda x,p: x["nurses"][0].update(skills=["B"]),
            "wrong duration": lambda x,p: p["assignments"][0].update(end=21),
            "late finish": lambda x,p: x["tasks"][0].update(deadline=19),
            "outside availability": lambda x,p: x["nurses"][0].update(available_from=1),
            "capacity": lambda x,p: x["nurses"][0].update(max_capacity_min=19),
            "task during break": lambda x,p: p["assignments"][0].update(start=60,end=80),
            "missing break": lambda x,p: p["breaks"].pop(),
            "auto approval": lambda x,p: p.update(approval_required=False),
            "simultaneous breaks": lambda x,p: [b.update(start=60,end=75) for b in p["breaks"]],
            "skill coverage": lambda x,p: x["shift"]["coverage_rules"][0].update(required_skill="B"),
            "zone coverage": lambda x,p: x["shift"]["coverage_rules"][0].update(zone="W2"),
            "fractional time": lambda x,p: p["assignments"][0].update(start=0.5,end=20.5),
            "unknown nurse": lambda x,p: p["assignments"][0].update(nurse_id="N99"),
            "wrong zone": lambda x,p: x["patients"][0].update(zone="W2"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                instance, plan = sample()
                mutate(instance, plan)
                self.assertFalse(validate_plan(instance, plan)["valid"])

    def test_transition_must_occupy_time_and_counts_as_load(self):
        instance, plan = sample()
        instance["patients"].append({"patient_id":"P2", "room":"R2", "zone":"W1"})
        second = dict(instance["tasks"][0], task_id="T2", patient_id="P2")
        instance["tasks"].append(second)
        plan["assignments"].append({"task_id":"T2", "nurse_id":"N1", "start":20, "end":40})
        self.assertFalse(validate_plan(instance, plan)["valid"])
        plan["assignments"][-1].update(start=22,end=42)
        result = validate_plan(instance, plan)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["metrics"]["overhead_minutes"], 2)
        self.assertEqual(result["metrics"]["workload_minutes"]["N1"], 42)


if __name__ == "__main__":
    unittest.main()
