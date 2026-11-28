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
META = json.loads((ROOT / "codebase/L4/taxonomy_meta.json").read_text(encoding="utf-8"))


def _tier_from_meta(score):
    """Tier theo điểm cắt đã ship trong taxonomy_meta.json (độc lập sklearn)."""
    for tier, (lo, hi) in META["tier_score_ranges"].items():
        if lo <= score <= hi:
            return int(tier)
    raise AssertionError(f"score {score} ngoài mọi tier range")


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

    def test_weighted_baseline_valid_drafts(self):
        for cid, instance in CASES.items():
            plan = baseline_allocate(instance, balance="weight")
            self.assertEqual(plan["status"], "draft", f"{cid}: {plan.get('warnings')}")
            self.assertEqual(plan["method"], "baseline_patient_weight")
            self.assertTrue(validate_plan(instance, plan)["valid"], cid)

    def test_unknown_balance_mode_is_labelled(self):
        # chế độ lạ vẫn gắn nhãn method rõ ràng (count-like vì weight_of=1 fallback).
        plan = baseline_allocate(CASES["P01"], balance="count")
        self.assertEqual(plan["method"], "baseline_patient_count")

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


class TaxonomyModel(unittest.TestCase):
    """L4 taxonomy đã ship (KMeans) + nhánh fallback — bất biến với/không có sklearn."""

    def _patient(self, acuity, adl, iso=False):
        return {"acuity_score": acuity, "adl_dependency": adl,
                "isolation_precaution": iso, "care_category": "medical"}

    def test_artifact_files_present(self):
        from baseline import _MODEL_PATH, _META_PATH
        self.assertTrue(_MODEL_PATH.exists(), "thiếu taxonomy_model.pkl đã ship")
        self.assertTrue(_META_PATH.exists(), "thiếu taxonomy_meta.json")

    def test_classify_matches_shipped_ranges(self):
        # Dù chạy nhánh model hay fallback, tier phải khớp ranges đã ship.
        for acuity in range(1, 6):
            for adl in range(1, 5):
                for iso in (0, 1):
                    score = acuity + adl + iso
                    tier = classify_patient(self._patient(acuity, adl, bool(iso)))["tier"]
                    self.assertEqual(tier, _tier_from_meta(score),
                                     f"a{acuity} d{adl} i{iso} (score {score})")

    def test_fallback_in_sync_with_model(self):
        # _fallback_tier (stdlib) phải cho đúng kết quả như ranges model đã học.
        from baseline import _fallback_tier
        for score in range(2, 11):
            self.assertEqual(_fallback_tier(score), _tier_from_meta(score), f"score {score}")

    def test_tier_monotonic_in_weight(self):
        prev = 0
        for score in range(2, 11):
            tier = _tier_from_meta(score)
            self.assertGreaterEqual(tier, prev, f"tier giảm tại score {score}")
            prev = tier

    def test_fixtures_agree_with_recorded_report(self):
        # meta ghi 6/6 khớp rule; classify hiện tại cũng phải cho đúng model_tier đó.
        for row in META["fixture_report"]:
            tier = classify_patient(self._patient(
                row["acuity"], row["adl"], bool(row["isolation"])))["tier"]
            self.assertEqual(tier, row["model_tier"], row)


if __name__ == "__main__":
    unittest.main()
