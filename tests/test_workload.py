"""Test L3 estimate_duration. Số phút trong file này là giá trị kiểm thử, không phải dữ liệu thật."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
from workload import (DurationNeedInfo, InvalidInstance, LookupTableEstimator, MedianBaseline,
                      SimmonsLookupEstimator, SourceTableError, assess_durations,
                      estimate_duration)
from workload.evaluation import group_split, leakage_issues, metrics_by_group, regression_metrics
from workload.models import DurationEstimator, load_metadata

TEST_CITATION = "test-only, không phải số liệu thật"


def instance(*tasks):
    return {
        "shift": {"shift_id": "S1", "ward_id": "W1", "shift_length_min": 120},
        "nurses": [{"nurse_id": "N1", "skills": ["A"], "home_zone": "W1"}],
        "patients": [{"patient_id": "P1", "room": "R1", "zone": "W1", "acuity_score": 2}],
        "tasks": list(tasks),
    }


def task(task_id="T1", **extra):
    row = {"task_id": task_id, "patient_id": "P1", "task_type": "vitals",
           "required_skill": ["A"], "earliest_start": 0, "deadline": 60, "mandatory": True}
    row.update(extra)
    return row


def lookup(by=None):
    table = {("vitals", 2): 12} if by else {"vitals": 10}
    return LookupTableEstimator("test", TEST_CITATION, table, by=by)


class GivenDurationTests(unittest.TestCase):
    def test_1_valid_duration_is_kept(self):
        result = estimate_duration(instance(task(est_duration_min=15)))
        self.assertEqual(result["tasks"][0]["est_duration_min"], 15)
        self.assertEqual(result["tasks"][0]["duration_source"], "given")

    def test_2_many_valid_durations_are_kept(self):
        tasks = [task("T%d" % i, est_duration_min=5 * i) for i in range(1, 6)]
        report = assess_durations(instance(*tasks))
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["kept"], ["T1", "T2", "T3", "T4", "T5"])
        self.assertEqual([t["est_duration_min"] for t in report["instance"]["tasks"]], [5, 10, 15, 20, 25])
        self.assertEqual(report["estimated"], [])

    def test_10_given_duration_and_source_never_overwritten(self):
        data = instance(task(est_duration_min=33, duration_source="provided_synthetic"))
        result = estimate_duration(data, estimators=[lookup()])
        self.assertEqual(result["tasks"][0]["est_duration_min"], 33)
        self.assertEqual(result["tasks"][0]["duration_source"], "provided_synthetic")


class MissingDurationTests(unittest.TestCase):
    def test_3_missing_duration_without_estimator_asks_back(self):
        with self.assertRaises(DurationNeedInfo) as ctx:
            estimate_duration(instance(task()), estimators=[])
        self.assertIn("tasks.T1.est_duration_min", ctx.exception.missing_fields[0])
        self.assertIn("chưa có model", ctx.exception.missing_fields[0])

    def test_4_unsupported_task_type(self):
        report = assess_durations(instance(task(task_type="unknown_type")), estimators=[lookup()])
        self.assertEqual(report["status"], "need_info")
        self.assertIn("unknown_type", report["missing_fields"][0])
        self.assertIsNone(report["instance"])

    def test_8_missing_required_feature(self):
        data = instance(task())
        del data["patients"][0]["acuity_score"]
        report = assess_durations(data, estimators=[lookup(by="acuity_score")])
        self.assertEqual(report["status"], "need_info")
        self.assertTrue(any("acuity_score" in m for m in report["missing_fields"]))

    def test_estimate_with_sourced_lookup(self):
        result = estimate_duration(instance(task()), estimators=[lookup(by="acuity_score")])
        self.assertEqual(result["tasks"][0]["est_duration_min"], 12)
        self.assertEqual(result["tasks"][0]["duration_source"], "lookup:test")

    def test_partial_fill_is_not_returned_when_any_task_missing(self):
        data = instance(task("T1"), task("T2", task_type="unknown_type"))
        report = assess_durations(data, estimators=[lookup()])
        self.assertEqual(report["status"], "need_info")
        self.assertEqual(report["estimated"], [])
        self.assertIsNone(report["instance"])


class InvalidValueTests(unittest.TestCase):
    def assert_rejected(self, value):
        report = assess_durations(instance(task(est_duration_min=value)), estimators=[lookup()])
        self.assertEqual(report["status"], "need_info", value)
        self.assertIn("không hợp lệ", report["missing_fields"][0])

    def test_5_zero(self):
        self.assert_rejected(0)

    def test_6_negative(self):
        self.assert_rejected(-10)

    def test_7_wrong_types(self):
        for value in ("15", 15.5, 15.0, True, [15], {"min": 15}):
            with self.subTest(value=value):
                self.assert_rejected(value)

    def test_9_invalid_instance(self):
        for bad in (None, "lập ca", [], {}, {"tasks": []}, {"tasks": ["T1"]},
                    {"tasks": [{"task_type": "vitals"}]}):
            with self.subTest(bad=bad):
                with self.assertRaises(InvalidInstance):
                    estimate_duration(bad)

    def test_estimator_returning_bad_value_is_ignored(self):
        class Broken(DurationEstimator):
            source = "model:broken-test"
            required_features = ("task_type",)
            def supports(self, task_type):
                return True
            def predict(self, features):
                return 0
        report = assess_durations(instance(task()), estimators=[Broken()])
        self.assertEqual(report["status"], "need_info")


class BoundaryTests(unittest.TestCase):
    def test_11_input_not_mutated_and_only_l3_fields_change(self):
        data = instance(task("T1"), task("T2", est_duration_min=8))
        before = copy.deepcopy(data)
        result = estimate_duration(data, estimators=[lookup()])
        self.assertEqual(data, before)
        for old, new in zip(before["tasks"], result["tasks"]):
            changed = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
            self.assertLessEqual(changed, {"est_duration_min", "duration_source"})
        for key in ("shift", "nurses", "patients"):
            self.assertEqual(result[key], before[key])

    def test_12_no_new_tasks_nurses_or_skills(self):
        data = instance(task("T1", required_skill=["A"]))
        result = estimate_duration(data, estimators=[lookup()])
        self.assertEqual([t["task_id"] for t in result["tasks"]], ["T1"])
        self.assertEqual(result["nurses"], data["nurses"])
        self.assertEqual(result["tasks"][0]["required_skill"], ["A"])

    def test_12b_missing_required_skill_is_not_invented(self):
        row = task()
        del row["required_skill"]
        result = estimate_duration(instance(row), estimators=[lookup()])
        self.assertNotIn("required_skill", result["tasks"][0])

    def test_13_every_filled_duration_has_a_source(self):
        result = estimate_duration(instance(task(), task("T2", est_duration_min=4)), estimators=[lookup()])
        for row in result["tasks"]:
            self.assertTrue(row["duration_source"])
        with self.assertRaises(ValueError):
            LookupTableEstimator("no-source", "", {"vitals": 10})
        report = assess_durations(instance(task(duration_source="lookup:x")), estimators=[lookup()])
        self.assertEqual(report["status"], "need_info")

    def test_14_event_timestamps_never_become_duration(self):
        row = task(charttime=100, storetime=135, starttime=0, endtime=240)
        report = assess_durations(instance(row), estimators=[])
        self.assertEqual(report["status"], "need_info")
        report = assess_durations(instance(row), estimators=[lookup()])
        self.assertEqual(report["instance"]["tasks"][0]["est_duration_min"], 10)
        self.assertNotIn(35, [t["est_duration_min"] for t in report["instance"]["tasks"]])
        for name in ("charttime", "storetime", "starttime", "endtime", "actual_duration_min"):
            class Leaky(DurationEstimator):
                source = "model:leaky-test"
                required_features = ("task_type", name)
            with self.subTest(feature=name), self.assertRaises(ValueError):
                Leaky()

    def test_cp2_fixtures_keep_their_durations(self):
        cases = json.loads((ROOT / "data/cp2-cases.json").read_text(encoding="utf-8"))
        for case in cases:
            data = case["input"]
            if not isinstance(data, dict) or not data.get("tasks"):
                continue
            durations = [t.get("est_duration_min") for t in data["tasks"]]
            if not all(type(d) is int and d > 0 for d in durations):
                continue
            with self.subTest(case=case["id"]):
                result = estimate_duration(data)
                self.assertEqual([t["est_duration_min"] for t in result["tasks"]], durations)


class ModelAndEvaluationTests(unittest.TestCase):
    def test_median_baseline_rounds_up(self):
        model = MedianBaseline.fit([("vitals", 10), ("vitals", 11)], version="test")
        self.assertEqual(model.predict({"task_type": "vitals"}), 11)
        self.assertEqual(model.source, "model:median-test")
        with self.assertRaises(ValueError):
            MedianBaseline.fit([("vitals", 0)], version="test")

    def test_lookup_from_json_requires_citation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "table.json"
            path.write_text(json.dumps({"name": "t", "rows": [{"task_type": "vitals", "minutes": 9}]}))
            with self.assertRaises(ValueError):
                LookupTableEstimator.from_json(path)

    def test_metadata_rejects_forbidden_features(self):
        meta = {"model_version": "v0", "algorithm": "median", "target": "actual_duration_min",
                "features": ["task_type", "charttime"], "trained_on": "x", "trained_at": "x",
                "data_card": "x"}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "meta.json"
            path.write_text(json.dumps(meta))
            with self.assertRaises(ValueError):
                load_metadata(path)

    def test_metrics_report_underestimation(self):
        result = regression_metrics([10, 20, 30], [12, 15, 30])
        self.assertAlmostEqual(result["mae"], 7 / 3)
        self.assertAlmostEqual(result["underestimate_rate"], 1 / 3)
        self.assertEqual(result["max_underestimate_min"], 5)
        groups = metrics_by_group([10, 20], [10, 25], ["a", "b"])
        self.assertEqual(groups["b"]["mae"], 5)

    def test_group_split_has_no_shared_patients(self):
        rows = [{"patient_id": "P%d" % (i % 5), "y": i} for i in range(20)]
        train, test = group_split(rows, "patient_id")
        self.assertEqual(leakage_issues(["task_type"], train, test, "patient_id"), [])
        self.assertTrue(leakage_issues(["storetime"]))


BUNDLE = ROOT / "data" / "preliminary" / "instances.json"
SIMMONS = "lookup:simmons-2025-table3"


def ward_task(task_id, task_type, **extra):
    return task(task_id, task_type=task_type, **extra)


class PreliminaryContractTests(unittest.TestCase):
    """Contract test với bộ bàn giao của Lam/Kiên: l3_input → đúng bằng instance mong đợi."""

    @classmethod
    def setUpClass(cls):
        cls.bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
        cls.cases = {c["id"]: c for c in cls.bundle["cases"]}

    def run_case(self, case_id):
        case = copy.deepcopy(self.cases[case_id])
        before = copy.deepcopy(case["l3_input"])
        result = estimate_duration(case["l3_input"])
        self.assertEqual(case["l3_input"], before, "L3 sửa input gốc")
        self.assertEqual(result, case["instance"])
        return case, result

    def test_p01_keeps_all_given_durations(self):
        _, result = self.run_case("P01")
        self.assertEqual({t["duration_source"] for t in result["tasks"]}, {"given"})
        self.assertEqual({t["est_duration_min"] for t in result["tasks"]}, {10})

    def test_p02_keeps_t1_and_fills_five_from_simmons(self):
        _, result = self.run_case("P02")
        tasks = {t["task_id"]: t for t in result["tasks"]}
        self.assertEqual((tasks["T1"]["est_duration_min"], tasks["T1"]["duration_source"]), (10, "given"))
        filled = [t for t in result["tasks"] if t["task_id"] != "T1"]
        self.assertEqual(len(filled), 5)
        self.assertTrue(all(t["duration_source"] == SIMMONS for t in filled))

    def test_p03_keeps_roster_without_absent_nurse(self):
        case, result = self.run_case("P03")
        ids = [n["nurse_id"] for n in result["nurses"]]
        self.assertNotIn(case["absent_nurse_id"], ids)
        self.assertEqual(result["nurses"], case["l3_input"]["nurses"])

    def test_simmons_csv_matches_bundle_checksum(self):
        estimator = SimmonsLookupEstimator()
        self.assertEqual(estimator.sha256, self.bundle["source_sha256"]["ward_task_duration.csv"])


class SimmonsLookupTests(unittest.TestCase):
    def setUp(self):
        self.simmons = SimmonsLookupEstimator()

    def fill(self, *tasks):
        return assess_durations(instance(*tasks), estimators=[self.simmons])

    def test_values_are_read_from_csv_and_rounded_up(self):
        import csv
        import math
        with open(ROOT / "data/reference/ward_task_duration.csv", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                with self.subTest(task_type=row["task_type"]):
                    self.assertEqual(self.simmons.rows[row["task_type"]]["minutes"],
                                     math.ceil(float(row["mean_duration_min"])))

    def test_seven_single_staff_types_fill_without_extra_fields(self):
        for task_type in ("med_admin", "wound_care", "iv_care", "procedure_care", "vitals",
                          "lab_collection", "catheter_care"):
            with self.subTest(task_type=task_type):
                report = self.fill(ward_task("T1", task_type))
                self.assertEqual(report["status"], "ok", report["missing_fields"])
                self.assertEqual(report["estimated"][0]["duration_source"], SIMMONS)

    def test_task_not_in_table(self):
        for task_type in ("medication_preparation", "handover", "documentation", "Vitals", "vital"):
            with self.subTest(task_type=task_type):
                report = self.fill(ward_task("T1", task_type))
                self.assertEqual(report["status"], "need_info")
                self.assertIn("chưa được L3 hỗ trợ", report["missing_fields"][0])

    def test_medication_preparation_never_uses_med_admin_mean(self):
        report = self.fill(ward_task("T1", "medication_preparation", task_name="Medication Preparation"))
        self.assertEqual(report["status"], "need_info")
        self.assertEqual(report["estimated"], [])

    def test_two_staff_tasks_need_confirmation(self):
        for task_type, extra in (("toileting", {}), ("mobilization", {"mobility_scope": "walking"})):
            with self.subTest(task_type=task_type):
                report = self.fill(ward_task("T1", task_type, **extra))
                self.assertEqual(report["status"], "need_info")
                self.assertTrue(any("staff_required" in m for m in report["missing_fields"]))
        report = self.fill(ward_task("T1", "toileting", staff_required=1))
        self.assertEqual(report["estimated"][0]["est_duration_min"], 6)

    def test_task_needing_two_staff_is_not_scheduled_as_one(self):
        for task_type in ("toileting", "vitals"):
            with self.subTest(task_type=task_type):
                report = self.fill(ward_task("T1", task_type, staff_required=2))
                self.assertEqual(report["status"], "need_info")
                self.assertIn("schema hiện chưa hỗ trợ", " ".join(report["missing_fields"]))

    def test_mobility_outside_source_definition(self):
        for scope in (None, "transport", "transfer_lift", "repositioning"):
            with self.subTest(scope=scope):
                extra = {"staff_required": 1}
                if scope:
                    extra["mobility_scope"] = scope
                report = self.fill(ward_task("T1", "mobilization", **extra))
                self.assertEqual(report["status"], "need_info")
                self.assertTrue(any("mobility_scope" in m for m in report["missing_fields"]))
        report = self.fill(ward_task("T1", "mobilization", staff_required=1, mobility_scope="bed_to_chair"))
        self.assertEqual(report["estimated"][0]["est_duration_min"], 3)

    def test_unconfirmed_or_out_of_scope_conditions(self):
        for extra in ({"setting": "operating_room"}, {"complexity": "complex"},
                      {"synchronization": ["T2"]}):
            with self.subTest(extra=extra):
                report = self.fill(ward_task("T1", "procedure_care", **extra))
                self.assertEqual(report["status"], "need_info")
        report = self.fill(ward_task("T1", "procedure_care", setting="inpatient_ward", complexity="standard"))
        self.assertEqual(report["status"], "ok")

    def test_no_acuity_or_adl_adjustment(self):
        data = instance(ward_task("T1", "vitals"))
        results = set()
        for acuity, adl in ((1, 1), (5, 4)):
            data["patients"][0].update(acuity_score=acuity, adl_dependency=adl)
            results.add(estimate_duration(data, estimators=[self.simmons])["tasks"][0]["est_duration_min"])
        self.assertEqual(results, {4})

    def test_mixed_given_and_lookup(self):
        report = self.fill(ward_task("T1", "vitals", est_duration_min=25),
                           ward_task("T2", "vitals"), ward_task("T3", "wound_care", est_duration_min=9,
                                                                duration_source="provided_synthetic"))
        tasks = {t["task_id"]: t for t in report["instance"]["tasks"]}
        self.assertEqual((tasks["T1"]["est_duration_min"], tasks["T1"]["duration_source"]), (25, "given"))
        self.assertEqual((tasks["T2"]["est_duration_min"], tasks["T2"]["duration_source"]), (4, SIMMONS))
        self.assertEqual(tasks["T3"]["duration_source"], "provided_synthetic")
        self.assertEqual(report["kept"], ["T1", "T3"])

    def test_invalid_duration_source(self):
        for source in ("", "   ", 5, ["given"]):
            with self.subTest(source=source):
                report = self.fill(ward_task("T1", "vitals", est_duration_min=5, duration_source=source))
                self.assertEqual(report["status"], "need_info")
                self.assertIn("duration_source", report["missing_fields"][0])

    def test_timestamps_on_task_do_not_change_lookup(self):
        report = self.fill(ward_task("T1", "med_admin", charttime=0, storetime=45,
                                     starttime=0, endtime=300))
        self.assertEqual(report["instance"]["tasks"][0]["est_duration_min"], 7)

    def test_need_info_instance_never_reaches_solver(self):
        report = self.fill(ward_task("T1", "vitals"), ward_task("T2", "toileting"))
        self.assertIsNone(report["instance"])
        with self.assertRaises(DurationNeedInfo) as ctx:
            estimate_duration(instance(ward_task("T1", "vitals"), ward_task("T2", "toileting")),
                              estimators=[self.simmons])
        self.assertIsNone(ctx.exception.report["instance"])


class ProductionBoundaryTests(unittest.TestCase):
    def test_production_defaults_are_simmons_only(self):
        from workload.models import default_estimators
        self.assertEqual([e.source for e in default_estimators()], [SIMMONS])

    def test_production_code_never_loads_experimental_or_model(self):
        for path in (ROOT / "codebase" / "workload").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotIn("artifacts", text)
                self.assertNotIn("or_ridge", text)
        meta = ROOT / "artifacts" / "l3" / "or_ridge_v1.metadata.json"
        if meta.exists():
            self.assertIs(json.loads(meta.read_text(encoding="utf-8"))["production"], False)


class SourceTableTests(unittest.TestCase):
    HEADER = ("task_type,source_task,mean_duration_min,sd_min,min_min,max_min,unit,statistic,"
              "source_table,source_doi,context,data_kind,staffing_note\n")
    ROW = ("vitals,Vitals Assessments,{mean},2.51,0.1,16.9,minutes_per_patient_episode,observed_mean,3,"
           "10.1111/jgs.19507,US_ACE_older_acute_inpatients,published_aggregate,skills_and_roster_must_be_given\n")

    def load(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "table.csv"
            path.write_text(text, encoding="utf-8")
            return SimmonsLookupEstimator(path)

    def test_valid_temp_table(self):
        self.assertEqual(self.load(self.HEADER + self.ROW.format(mean="3.01")).rows["vitals"]["minutes"], 4)

    def test_broken_tables_raise_source_error(self):
        cases = {
            "missing file": None,
            "empty": self.HEADER,
            "missing column": self.HEADER.replace(",staffing_note", "") + self.ROW.format(mean="3"),
            "non numeric": self.HEADER + self.ROW.format(mean="abc"),
            "zero": self.HEADER + self.ROW.format(mean="0"),
            "duplicate": self.HEADER + self.ROW.format(mean="3") * 2,
            "wrong unit": self.HEADER + self.ROW.format(mean="3").replace("minutes_per_patient_episode", "hours"),
        }
        for name, text in cases.items():
            with self.subTest(case=name), self.assertRaises(SourceTableError):
                if text is None:
                    SimmonsLookupEstimator(Path(tempfile.gettempdir()) / "khong-ton-tai.csv")
                else:
                    self.load(text)


if __name__ == "__main__":
    unittest.main()
