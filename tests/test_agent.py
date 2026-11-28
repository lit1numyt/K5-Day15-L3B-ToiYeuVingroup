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
from agent import _LAST_SESSION, answer  # noqa: E402
from planning import validate_plan  # noqa: E402


class AgentTests(unittest.TestCase):
    def setUp(self):
        _LAST_SESSION.clear()
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

    def test_nl_refuses_clinical_and_safety_override_requests(self):
        reply = {
            "text": json.dumps({
                "intent": "refuse",
                "reason": "Không tư vấn chọn thuốc hay liều dùng vì đây là quyết định lâm sàng.",
                "refusal_category": "clinical_decision",
                "redirect_to": "bác sĩ hoặc điều dưỡng có thẩm quyền",
            }, ensure_ascii=False),
            "model": "mock-real",
            "tokens_in": 80,
            "tokens_out": 40,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=reply),
        ):
            result = json.loads(answer("Bệnh nhân sốt cao nên dùng thuốc gì?")["output"])
        self.assertEqual(result["status"], "refused")
        self.assertIs(result["approval_required"], True)
        self.assertFalse(result.get("assignments"))
        self.assertIn("bác sĩ", result["explanation"].lower())

    def test_nl_need_info_for_missing_skills_and_data_traps(self):
        reply = {
            "text": json.dumps({
                "intent": "need_info",
                "reason": "Thiếu danh sách kỹ năng bắt buộc cho từng task.",
                "missing_fields": ["tasks.required_skill: cần kỹ năng yêu cầu của từng công việc"],
                "questions": ["Mỗi công việc trong ca cần kỹ năng nào?"],
            }, ensure_ascii=False),
            "model": "mock-real",
            "tokens_in": 90,
            "tokens_out": 45,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=reply),
        ):
            result = json.loads(answer("Có 3 điều dưỡng và 6 task nhưng chưa ghi kỹ năng.")["output"])
        self.assertEqual(result["status"], "need_info")
        self.assertFalse(result.get("assignments"))
        self.assertTrue(result["missing_fields"])

    def test_nl_infeasible_overload_returns_infeasible_without_assignments(self):
        reply = {
            "text": json.dumps({
                "intent": "infeasible",
                "conflict_summary": "20 task bắt buộc dồn trong 60 phút vượt quá năng lực 2 điều dưỡng.",
                "relaxation_options": ["Bổ sung thêm điều dưỡng trực", "Giãn deadline một số task"],
            }, ensure_ascii=False),
            "model": "mock-real",
            "tokens_in": 95,
            "tokens_out": 50,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=reply),
        ):
            result = json.loads(answer("2 điều dưỡng, 20 task bắt buộc trong khung 8h-9h.")["output"])
        self.assertEqual(result["status"], "infeasible")
        self.assertFalse(result.get("assignments"))
        self.assertEqual(len(result["relaxation_options"]), 2)

    def test_nl_draft_filters_absent_and_hallucinated_nurses(self):
        reply = {
            "text": json.dumps({
                "intent": "plan_from_text",
                "absent_nurses": ["N3"],
                "draft_summary": {
                    "assignments": [
                        {"task": "tiêm", "nurse_id": "N1", "patient_id": "P1", "basis": "đủ kỹ năng"},
                        {"task": "thay băng", "nurse_id": "N3", "patient_id": "P2", "basis": "nhầm người vắng"},
                        {"task": "hô hấp", "nurse_id": "N9", "patient_id": "P2", "basis": "mã bịa"},
                    ],
                    "breaks": [{"nurse_id": "N1", "start_min": 60, "end_min": 75}],
                    "explanation": "Giao N1 thực hiện tiêm cho P1 theo đúng kỹ năng.",
                },
            }, ensure_ascii=False),
            "model": "mock-real",
            "tokens_in": 120,
            "tokens_out": 80,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=reply),
        ):
            result = json.loads(answer("N1, N2 trực; N3 vắng. Lập ca cho P1, P2.")["output"])
        self.assertEqual(result["status"], "draft")
        self.assertIs(result["approval_required"], True)
        assigned = {a["nurse_id"] for a in result["assignments"]}
        self.assertEqual(assigned, {"N1"})
        self.assertIn("N3", " ".join(result["warnings"]))
        self.assertIn("duyệt", result["explanation"].lower())

    def test_nl_explain_followup_tracks_last_session(self):
        bundle = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            first = json.loads(answer(json.dumps(bundle["cases"][0]["l3_input"], ensure_ascii=False))["output"])
        self.assertEqual(first["status"], "draft")
        self.assertTrue(_LAST_SESSION.get("plan"))

        followup = {
            "text": json.dumps({
                "intent": "explain_followup",
                "draft_summary": {
                    "explanation": "N1 nhận T1 cho P1 vì khớp kỹ năng med_admin và cân bằng tải ca S01."
                },
            }, ensure_ascii=False),
            "model": "mock-real",
            "tokens_in": 110,
            "tokens_out": 35,
        }
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "call_model", return_value=followup) as mocked,
        ):
            second = json.loads(answer("Vì sao N1 được giao T1?")["output"])
        self.assertEqual(second["status"], "draft")
        self.assertIn("N1", second["explanation"])
        sent_payload = json.loads(mocked.call_args[0][1])
        self.assertIsNotNone(sent_payload["session_context"])


if __name__ == "__main__":
    unittest.main()
