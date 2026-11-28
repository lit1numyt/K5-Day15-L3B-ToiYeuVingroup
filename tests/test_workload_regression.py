"""Regression cho các lỗi review PR #7 của L3. Số phút ở đây là giá trị kiểm thử."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
from workload import (DurationNeedInfo, InvalidInstance, SimmonsLookupEstimator, SourceTableError,
                      assess_durations, estimate_duration)

SIMMONS = "lookup:simmons-2025-table3"
BAD_VALUES = (True, False, 1.0, "1", 0, -1, [], {}, None, "")


def task(task_id="T01", **extra):
    row = {"task_id": task_id, "patient_id": "P1", "task_type": "vitals"}
    row.update(extra)
    return row


def instance(*tasks, **extra):
    data = {"patients": [{"patient_id": "P1"}], "tasks": list(tasks)}
    data.update(extra)
    return data


def status(*tasks, **extra):
    return assess_durations(instance(*tasks, **extra))


class DurationSourceNullTests(unittest.TestCase):
    """P1: duration_source=null + duration hợp lệ từng gây AssertionError."""

    def test_missing_or_null_source_becomes_given(self):
        for row in (task(est_duration_min=15), task(est_duration_min=15, duration_source=None)):
            with self.subTest(row=row):
                result = estimate_duration(instance(row))
                self.assertEqual((result["tasks"][0]["est_duration_min"], result["tasks"][0]["duration_source"]),
                                 (15, "given"))

    def test_blank_or_wrong_type_source_asks_back(self):
        for source in ("", "   ", 5, True, [], {}, ["given"]):
            with self.subTest(source=source):
                report = status(task(est_duration_min=15, duration_source=source))
                self.assertEqual(report["status"], "need_info")
                self.assertIn("duration_source", report["missing_fields"][0])

    def test_valid_source_is_kept(self):
        result = estimate_duration(instance(task(est_duration_min=15, duration_source="provided_synthetic")))
        self.assertEqual(result["tasks"][0]["duration_source"], "provided_synthetic")

    def test_source_without_duration_asks_back(self):
        report = status(task(duration_source="given"))
        self.assertEqual(report["status"], "need_info")
        self.assertIn("thiếu số phút", report["missing_fields"][0])

    def test_null_source_and_missing_duration_uses_lookup(self):
        result = estimate_duration(instance(task(duration_source=None)))
        self.assertEqual((result["tasks"][0]["est_duration_min"], result["tasks"][0]["duration_source"]),
                         (4, SIMMONS))


class MultiStaffSafetyTests(unittest.TestCase):
    """P1: task cần nhiều nhân viên không được xuống solver chỉ vì đã có duration."""

    def assert_blocked(self, row, field):
        report = status(row)
        self.assertEqual(report["status"], "need_info")
        self.assertIsNone(report["instance"])
        self.assertTrue(any(field in m for m in report["missing_fields"]), report["missing_fields"])
        with self.assertRaises(DurationNeedInfo):
            estimate_duration(instance(row))

    def test_1_two_staff_without_duration(self):
        self.assert_blocked(task(task_type="mobilization", staff_required=2, mobility_scope="walking"),
                            "staff_required")

    def test_2_two_staff_with_given_duration(self):
        self.assert_blocked(task(task_type="mobilization", staff_required=2, est_duration_min=15,
                                 duration_source="given"), "staff_required")

    def test_3_synchronization_without_duration(self):
        self.assert_blocked(task(synchronization=["T02"]), "synchronization")

    def test_4_synchronization_with_given_duration(self):
        self.assert_blocked(task(synchronization=["T02"], est_duration_min=15), "synchronization")

    def test_5_valid_single_staff(self):
        result = estimate_duration(instance(task(task_type="toileting", staff_required=1)))
        self.assertEqual(result["tasks"][0]["staff_required"], 1)
        self.assertEqual(result["tasks"][0]["est_duration_min"], 6)

    def test_6_plain_task_without_staffing_fields(self):
        result = estimate_duration(instance(task(est_duration_min=12)))
        self.assertNotIn("staff_required", result["tasks"][0])

    def test_7_mixed_instance_is_blocked_whole(self):
        data = instance(task("T01", est_duration_min=12), task("T02"),
                        task("T03", staff_required=2, est_duration_min=10))
        before = copy.deepcopy(data)
        report = assess_durations(data)
        self.assertEqual(report["status"], "need_info")
        self.assertEqual(report["estimated"], [])
        self.assertIsNone(report["instance"])
        self.assertEqual(data, before, "không được sửa staff_required hay input")

    def test_falsy_synchronization_matches_planning_convention(self):
        for value in (None, [], "", False, 0, {}):
            with self.subTest(value=value):
                self.assertEqual(status(task(synchronization=value, est_duration_min=5))["status"], "ok")


class ConditionFieldTypeTests(unittest.TestCase):
    """P2: True == 1, 1.0 == 1, list trong set — không được lọt hay gây TypeError."""

    def test_staff_required_types(self):
        for value in BAD_VALUES:
            with self.subTest(value=value):
                report = status(task(task_type="toileting", staff_required=value))
                self.assertEqual(report["status"], "need_info")   # None = chưa xác nhận → vẫn hỏi
                report = status(task(staff_required=value, est_duration_min=5))
                self.assertEqual(report["status"], "ok" if value is None else "need_info")

    def test_text_condition_fields_types(self):
        for field in ("mobility_scope", "setting", "complexity"):
            for value in BAD_VALUES:
                with self.subTest(field=field, value=value):
                    report = status(task(task_type="mobilization", staff_required=1, **{field: value}))
                    self.assertIn(report["status"], {"ok", "need_info"})
                    if value is not None and not isinstance(value, str) or value == "":
                        self.assertTrue(any(field in m for m in report["missing_fields"]))

    def test_estimate_never_crashes_on_bad_types(self):
        fields = ("staff_required", "mobility_scope", "setting", "complexity", "synchronization",
                  "est_duration_min", "duration_source", "task_type")
        for field in fields:
            for value in BAD_VALUES:
                for with_duration in (False, True):
                    row = task(task_type="mobilization")
                    if with_duration:
                        row["est_duration_min"] = 7
                    row[field] = value
                    with self.subTest(field=field, value=value, with_duration=with_duration):
                        try:
                            estimate_duration(instance(row))
                        except (DurationNeedInfo, InvalidInstance):
                            pass


class StructuralValidationTests(unittest.TestCase):
    """P2: patients/shift/patient_id sai kiểu từng gây TypeError."""

    def assert_invalid(self, data, needle):
        report = assess_durations(data)
        self.assertEqual(report["status"], "invalid_input", report)
        self.assertTrue(any(needle in m for m in report["missing_fields"]), report["missing_fields"])
        with self.assertRaises(InvalidInstance):
            estimate_duration(data)

    def test_patients_not_a_list(self):
        for value in (123, "P1", {"patient_id": "P1"}):
            with self.subTest(value=value):
                self.assert_invalid({"patients": value, "tasks": [task()]}, "patients")

    def test_patient_row_and_id_types(self):
        for rows in (["P1"], [5], [{"patient_id": ["P1"]}], [{"patient_id": 1}], [{"patient_id": ""}],
                     [{"room": "R1"}], [{"patient_id": "P1"}, {"patient_id": "P1"}]):
            with self.subTest(rows=rows):
                self.assert_invalid({"patients": rows, "tasks": [task()]}, "patients")

    def test_duplicate_or_blank_task_id(self):
        self.assert_invalid(instance(task("T01", est_duration_min=5), task("T01", est_duration_min=6)), "trùng")
        self.assert_invalid(instance(task("   ", est_duration_min=5)), "task_id")

    def test_task_patient_id_type(self):
        for value in ([], {}, 7, ""):
            with self.subTest(value=value):
                self.assert_invalid(instance(task(patient_id=value)), "patient_id")

    def test_shift_type(self):
        for value in ("abc", 5, []):
            with self.subTest(value=value):
                self.assert_invalid(instance(task(est_duration_min=5), shift=value), "shift")

    def test_non_object_or_unparsed_json(self):
        for value in ("{bad json", b"{}", 42, None, [task()]):
            with self.subTest(value=value):
                self.assert_invalid(value, "input")

    def test_valid_minimal_shapes_still_work(self):
        result = estimate_duration({"tasks": [task(est_duration_min=5)]})   # không có patients/shift
        self.assertEqual(result["tasks"][0]["duration_source"], "given")


class DurationSourceVerificationTests(unittest.TestCase):
    """P2: phân biệt nguồn đã biết, nguồn chưa xác minh và nguồn L3 tự tạo."""

    def test_known_sources_kept_without_warning(self):
        for source in ("given", "provided_synthetic", SIMMONS):
            with self.subTest(source=source):
                report = status(task(est_duration_min=5, duration_source=source))
                self.assertEqual(report["status"], "ok")
                self.assertEqual(report["instance"]["tasks"][0]["duration_source"], source)
                self.assertEqual(report["unverified_sources"], [])
                self.assertEqual(report["estimated"], [])   # input cung cấp, không phải L3 tạo

    def test_unknown_source_kept_but_flagged(self):
        report = status(task(est_duration_min=5, duration_source="nurse-memory"))
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["instance"]["tasks"][0]["duration_source"], "nurse-memory")
        self.assertEqual(report["unverified_sources"], ["T01"])
        self.assertTrue(any("chưa có trong danh sách" in w for w in report["warnings"]))

    def test_l3_only_writes_lookup_source_when_it_looked_up(self):
        report = status(task("T01", est_duration_min=5), task("T02"))
        sources = {t["task_id"]: t["duration_source"] for t in report["instance"]["tasks"]}
        self.assertEqual(sources, {"T01": "given", "T02": SIMMONS})
        self.assertEqual([e["task_id"] for e in report["estimated"]], ["T02"])

    def test_blank_null_and_wrong_type(self):
        self.assertEqual(status(task(est_duration_min=5, duration_source=None))["status"], "ok")
        for source in ("", 3, ["given"]):
            with self.subTest(source=source):
                self.assertEqual(status(task(est_duration_min=5, duration_source=source))["status"], "need_info")


class SimmonsTableIntegrityTests(unittest.TestCase):
    HEADER = ("task_type,source_task,mean_duration_min,sd_min,min_min,max_min,unit,statistic,"
              "source_table,source_doi,context,data_kind,staffing_note\n")

    def row(self, mean="3.65", table="3", doi="10.1111/jgs.19507", note="skills_and_roster_must_be_given",
            source_task="Vitals Assessments"):
        return ("vitals,%s,%s,2.51,0.1,16.9,minutes_per_patient_episode,observed_mean,%s,%s,"
                "US_ACE_older_acute_inpatients,published_aggregate,%s\n" % (source_task, mean, table, doi, note))

    def load(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "t.csv"
            path.write_text(text, encoding="utf-8")
            return SimmonsLookupEstimator(path)

    def test_valid_row_still_loads(self):
        self.assertEqual(self.load(self.HEADER + self.row()).rows["vitals"]["minutes"], 4)

    def test_bad_rows_raise_source_table_error(self):
        cases = {
            "NaN": self.row(mean="NaN"), "Infinity": self.row(mean="Infinity"),
            "-Infinity": self.row(mean="-Infinity"), "sNaN": self.row(mean="sNaN"),
            "empty mean": self.row(mean=""), "negative": self.row(mean="-2"), "zero": self.row(mean="0"),
            "empty staffing_note": self.row(note=""), "empty source_task": self.row(source_task=""),
            "wrong doi": self.row(doi="10.9999/other"), "wrong table": self.row(table="4"),
            "short row": "vitals,Vitals Assessments,3.65\n",
        }
        for name, row in cases.items():
            with self.subTest(case=name), self.assertRaises(SourceTableError):
                self.load(self.HEADER + row)

    def test_source_error_is_not_disguised_as_need_info(self):
        broken = Path(tempfile.gettempdir()) / "khong-ton-tai-l3.csv"
        with self.assertRaises(SourceTableError):
            SimmonsLookupEstimator(broken)


if __name__ == "__main__":
    unittest.main()
