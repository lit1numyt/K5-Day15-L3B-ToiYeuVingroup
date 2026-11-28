"""Tests cho luồng L1 (agent.py) tích hợp L3 -> L2 -> validate_plan."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

import ai  # noqa: E402
from agent import answer  # noqa: E402
from planning import validate_plan  # noqa: E402


class AgentTests(unittest.TestCase):
    def test_cp2_cases_and_quality_anchors(self):
        cases = json.loads((ROOT / "data/cp2-cases.json").read_text(encoding="utf-8"))
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            for case in cases:
                with self.subTest(case=case["id"]):
                    result = json.loads(answer(json.dumps(case["input"], ensure_ascii=False))["output"])
                    self.assertEqual(result["status"], case["expected"])
                    self.assertEqual(result["mode"], "cp3")
                    self.assertIs(result["approval_required"], True)
                    if result["status"] == "draft":
                        validation = validate_plan(case["input"], result)
                        self.assertTrue(validation["valid"], validation)
                        if case["id"] == "F02":
                            self.assertLessEqual(validation["metrics"]["utilization_cv"], 0.10)
                        if case["id"] == "F03":
                            self.assertLessEqual(validation["metrics"]["overhead_minutes"], 2)

    def test_preliminary_cases_p01_to_p03_end_to_end_via_l3(self):
        bundle = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            for case in bundle["cases"]:
                with self.subTest(case=case["id"]):
                    payload = json.dumps(case["l3_input"], ensure_ascii=False)
                    result = json.loads(answer(payload)["output"])
                    self.assertEqual(result["status"], "draft", result.get("warnings"))
                    self.assertEqual(result["mode"], "cp3")
                    self.assertIs(result["approval_required"], True)
                    # Kiểm định trên instance kỳ vọng đã điền sẵn duration từ Simmons
                    validation = validate_plan(case["instance"], result)
                    self.assertTrue(validation["valid"], validation["violations"])
                    if case["id"] == "P03":
                        assigned_nurses = {a["nurse_id"] for a in result["assignments"]}
                        self.assertNotIn("N3", assigned_nurses)

    def test_l3_need_info_blocks_solver_for_toileting_or_multi_staff(self):
        bundle = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
        data = copy.deepcopy(bundle["cases"][1]["l3_input"])
        data["tasks"][1]["task_type"] = "toileting"
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            result = json.loads(answer(json.dumps(data, ensure_ascii=False))["output"])
        self.assertEqual(result["status"], "need_info")
        self.assertFalse(result.get("assignments"))
        self.assertTrue(any("staff_required" in m for m in result["missing_fields"]))

    def test_unstructured_input_asks_for_data(self):
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            result = json.loads(answer("lập ca cho tôi")["output"])
        self.assertEqual(result["status"], "need_info")
        message = " ".join(result["warnings"])
        self.assertIn("JSON", message)
        for field in ("shift", "nurses", "patients", "tasks"):
            self.assertIn(field, message)
        self.assertFalse(result.get("assignments"))

    def test_arbitrary_new_ids_do_not_lookup_fixture_answers(self):
        data = json.loads((ROOT / "data/cp2-cases.json").read_text(encoding="utf-8"))[0]["input"]
        data["tasks"][0]["task_id"] = "NEW-TASK"
        data["tasks"][0]["est_duration_min"] = 7
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            result = json.loads(answer(json.dumps(data))["output"])
        self.assertEqual(result["status"], "draft")
        entry = next(a for a in result["assignments"] if a["task_id"] == "NEW-TASK")
        self.assertEqual(entry["end"] - entry["start"], 7)

    def test_real_provider_uses_llm_explanation_and_guards_hallucinated_ids(self):
        bundle = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
        case_input = json.dumps(bundle["cases"][0]["l3_input"], ensure_ascii=False)
        valid_reply = {
            "text": "Đã giao T1 cho N1 (khớp kỹ năng med_admin, tải cân bằng). Bản nháp chờ trưởng ca duyệt.",
            "model": "mock-real",
            "tokens_in": 100,
            "tokens_out": 30,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=valid_reply) as mocked,
        ):
            result = json.loads(answer(case_input)["output"])
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(result["explanation"], valid_reply["text"])

        hallucinated_reply = {
            "text": "Đã giao T1 cho N99 để hỗ trợ N1.",
            "model": "mock-real",
            "tokens_in": 100,
            "tokens_out": 20,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=hallucinated_reply),
        ):
            result_guarded = json.loads(answer(case_input)["output"])
        self.assertNotIn("N99", result_guarded["explanation"])
        self.assertIn("trưởng ca duyệt", result_guarded["explanation"])


if __name__ == "__main__":
    unittest.main()
