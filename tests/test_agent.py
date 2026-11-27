import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"codebase"))
from agent import answer
from planning import validate_plan


class AgentTests(unittest.TestCase):
    def test_cp2_cases_and_quality_anchors(self):
        cases=json.loads((ROOT/"data/cp2-cases.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["id"]):
                result=json.loads(answer(json.dumps(case["input"],ensure_ascii=False))["output"])
                self.assertEqual(result["status"],case["expected"])
                self.assertEqual(result["mode"],"cp2")
                if result["status"]=="draft":
                    validation=validate_plan(case["input"],result)
                    self.assertTrue(validation["valid"],validation)
                    if case["id"]=="F02":
                        self.assertLessEqual(validation["metrics"]["utilization_cv"],0.10)
                    if case["id"]=="F03":
                        self.assertLessEqual(validation["metrics"]["overhead_minutes"],2)

    def test_unstructured_input_asks_for_data(self):
        result=json.loads(answer("lập ca cho tôi")["output"])
        self.assertEqual(result["status"],"need_info")

    def test_arbitrary_new_ids_do_not_lookup_fixture_answers(self):
        data=json.loads((ROOT/"data/cp2-cases.json").read_text(encoding="utf-8"))[0]["input"]
        data["tasks"][0]["task_id"]="NEW-TASK"
        data["tasks"][0]["est_duration_min"]=7
        result=json.loads(answer(json.dumps(data))["output"])
        self.assertEqual(result["status"],"draft")
        entry=next(a for a in result["assignments"] if a["task_id"]=="NEW-TASK")
        self.assertEqual(entry["end"]-entry["start"],7)
