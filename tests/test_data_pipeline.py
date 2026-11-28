"""Regression cho nhãn và thời gian quan sát; fixture tính tay, không có bệnh nhân thật."""
import csv
import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "translate_zenodo", ROOT / "scripts/data/translate_zenodo.py"
)
zenodo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(zenodo)


def segment(start, end, name="薬剤準備", duration=10):
    return [
        "45481", "1", str(start / 1440), str(end / 1440),
        f"{int(start % 1440 // 60)}時", str(duration / 1440),
        "看護", "準備（看）", name, "≪,≫", str(20 / 24), "", "",
    ]


def write_workbook(path, rows):
    """XLSX minimal có shared strings, theo cùng schema công khai 13 cột."""
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    strings = []
    shared = ET.Element("sst", xmlns=ns)
    sheet = ET.Element("worksheet", xmlns=ns)
    data = ET.SubElement(sheet, "sheetData")
    for number, values in enumerate([list(zenodo.COLUMN_MAP), *rows], 1):
        if values is None:  # Excel can omit entirely blank rows from the XML.
            continue
        row = ET.SubElement(data, "row", r=str(number))
        for col, value in enumerate(values):
            cell = ET.SubElement(row, "c", r=f"{chr(65 + col)}{number}", t="s")
            ET.SubElement(cell, "v").text = str(len(strings))
            strings.append(value)
            ET.SubElement(ET.SubElement(shared, "si"), "t").text = value
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", ET.tostring(shared))
        archive.writestr("xl/worksheets/sheet1.xml", ET.tostring(sheet))


class PipelineTests(unittest.TestCase):
    def convert(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            write_workbook(path / "source.xlsx", rows)
            result = zenodo.translate_dataset(
                path / "source.xlsx", path / "segments.csv", path / "glossary.json"
            )
            with (path / "segments.csv").open(newline="", encoding="utf-8") as f:
                segments = list(csv.DictReader(f))
            with (path / "zenodo_task_episodes_en.csv").open(
                newline="", encoding="utf-8"
            ) as f:
                episodes = list(csv.DictReader(f))
        return result, segments, episodes

    def test_exact_duplicate_does_not_add_work_minutes(self):
        _, segments, episodes = self.convert([
            segment(600, 610), segment(600, 610), segment(610, 620)
        ])
        self.assertEqual(len(segments), 2)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(float(episodes[0]["episode_duration_min"]), 20)

    def test_midnight_contiguous_segments_keep_source_order(self):
        _, _, episodes = self.convert([
            segment(1420, 1430, "伝票整理"),
            segment(1430, 0), segment(0, 10),
        ])
        meds = [e for e in episodes if e["task_name"] == "Medication Preparation"]
        self.assertEqual(len(meds), 1)
        self.assertEqual(float(meds[0]["episode_duration_min"]), 20)

    def test_backwards_source_rows_are_not_accepted_as_midnight(self):
        with self.assertRaisesRegex(ValueError, "Source order"):
            self.convert([segment(600, 610), segment(590, 600)])

    def test_medication_preparation_keeps_its_meaning(self):
        _, segments, _ = self.convert([segment(600, 610)])
        self.assertEqual(segments[0]["nurseflow_task_type"], "medication_preparation")

    def test_lineage_uses_physical_excel_row_after_blank(self):
        _, segments, episodes = self.convert([segment(600, 610), None, segment(610, 620)])
        self.assertEqual([int(s["source_excel_row"]) for s in segments], [2, 4])
        self.assertEqual(json.loads(episodes[0]["source_excel_rows"]), [2, 4])

    def test_local_shift_symbol_stays_a_source_identifier(self):
        source = segment(600, 610)
        source[9] = "●"
        _, segments, episodes = self.convert([source])
        self.assertEqual(segments[0]["shift_code"], "●")
        self.assertEqual(episodes[0]["shift_code"], "●")

    def test_missing_shift_end_stays_unknown(self):
        _, _, episodes = self.convert([segment(600, 610)])
        self.assertEqual(episodes[0]["shift_end_hhmmss"], "")
        self.assertEqual(episodes[0]["shift_length_min"], "")

    def test_patient_transport_is_not_bedside_mobility_assistance(self):
        _, segments, _ = self.convert([segment(600, 610, "患者搬送（応援）")])
        self.assertEqual(segments[0]["nurseflow_task_type"], "patient_transport")

    def test_missingness_audit_keeps_raw_denominator_before_deduplication(self):
        result, _, _ = self.convert([segment(600, 610), segment(600, 610)])
        self.assertEqual(result["raw_missing_counts"]["shift_end_raw"], 2)
        self.assertEqual(result["raw_records"], 2)

    def test_unrecorded_overtime_is_unknown_in_segments_and_episodes(self):
        _, segments, episodes = self.convert([segment(600, 610), segment(610, 620)])
        self.assertNotIn("is_overtime", segments[0])
        self.assertNotIn("is_overtime", episodes[0])
        self.assertEqual(segments[0]["overtime_status"], "Unspecified")
        self.assertEqual(episodes[0]["overtime_status"], "Unspecified")

    def test_recorded_overtime_flag_survives_episode_merge(self):
        flagged = segment(610, 620)
        flagged[-1] = "定時外"
        _, _, episodes = self.convert([segment(600, 610), flagged])
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["overtime_status"], "Overtime")

    def test_preparation_activity_does_not_invent_prep_requirement(self):
        work = segment(600, 610, "器械出し看護")
        work[7] = "手術関連業務（看）"
        _, segments, _ = self.convert([segment(590, 600), work])
        self.assertNotIn("prep_required", segments[0])
        self.assertEqual(int(segments[0]["is_preparation_activity"]), 1)
        self.assertEqual(int(segments[1]["is_preparation_activity"]), 0)

    def test_conference_information_and_education_keep_source_meaning(self):
        rows = [
            segment(600, 610, "部署内カンファレンス"),
            segment(610, 620, "担当患者情報収集"),
            segment(620, 630, "術前情報収集"),
            segment(630, 640, "手術介助見守り・補佐"),
        ]
        rows[-1][7] = "教育"
        _, segments, _ = self.convert(rows)
        self.assertEqual([s["nurseflow_task_type"] for s in segments], [
            "coordination", "information_gathering", "information_gathering", "education"
        ])

    def test_clean_rows_can_be_traced_to_excel_rows(self):
        _, segments, episodes = self.convert([segment(600, 610), segment(610, 620)])
        self.assertEqual([int(s["source_excel_row"]) for s in segments], [2, 3])
        self.assertEqual(json.loads(episodes[0]["source_excel_rows"]), [2, 3])


class FeatureTests(unittest.TestCase):
    def test_feature_build_needs_only_linked_observations(self):
        spec = importlib.util.spec_from_file_location(
            "preliminary_features", ROOT / "scripts/data/harmonize_and_engineer.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with (path / "zenodo_task_episodes_en.csv").open(
                "w", newline="", encoding="utf-8"
            ) as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "episode_id", "staff_id", "date", "task_name", "task_category",
                    "nurseflow_task_type", "episode_duration_min", "source_excel_rows",
                ])
                writer.writeheader()
                writer.writerow({
                    "episode_id": "E1", "staff_id": "S1", "date": "2024-07-08",
                    "task_name": "Medication Preparation", "task_category": "Preparation",
                    "nurseflow_task_type": "medication_preparation",
                    "episode_duration_min": 12, "source_excel_rows": "[2, 3]",
                })
                writer.writerow({
                    "episode_id": "E2", "staff_id": "S1", "date": "2024-07-08",
                    "task_name": "Break", "task_category": "Break",
                    "nurseflow_task_type": "break", "episode_duration_min": 15,
                    "source_excel_rows": "[4]",
                })
            module.build_harmonized_datasets(path)
            with (path / "l3_activity_features.csv").open(
                newline="", encoding="utf-8"
            ) as f:
                rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(float(rows[0]["actual_duration_min"]), 12)
        self.assertEqual(rows[0]["target_kind"], "observed_activity_episode")
        self.assertNotIn("patient_id", rows[0])
        self.assertNotIn("acuity_score", rows[0])
        self.assertNotIn("workload_points", rows[0])


class HandoffTests(unittest.TestCase):
    def test_handoff_checker_rejects_incomplete_pack_or_invalid_provenance(self):
        import copy
        spec = importlib.util.spec_from_file_location(
            "preliminary_checker", ROOT / "scripts/data/check_preliminary_handoff.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = json.loads((ROOT / "data/preliminary/instances.json").read_text(encoding="utf-8"))
        for change in [
            "empty_cases", "missing_case", "duplicate_case", "missing_checksums",
            "missing_taxonomy", "negative_experience", "changed_given", "wrong_absent_id",
            "missing_task_both", "lookup_became_given",
        ]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                bundle = copy.deepcopy(original)
                if change == "empty_cases":
                    bundle["cases"] = []
                elif change == "missing_case":
                    bundle["cases"].pop()
                elif change == "duplicate_case":
                    bundle["cases"][1]["id"] = "P01"
                elif change == "missing_checksums":
                    bundle["source_sha256"] = {}
                elif change == "wrong_absent_id":
                    bundle["cases"][-1]["absent_nurse_id"] = "NON_EXISTENT"
                else:
                    for case in bundle["cases"]:
                        for instance in [case["instance"], case["l3_input"]]:
                            if change == "missing_taxonomy":
                                for patient in instance["patients"]:
                                    patient.pop("acuity_score")
                            elif change == "negative_experience":
                                instance["nurses"][0]["experience_years"] = -10
                            elif change == "changed_given":
                                instance["tasks"][0]["est_duration_min"] = 11
                            elif change == "missing_task_both":
                                instance["tasks"].pop()
                            elif change == "lookup_became_given":
                                for task in instance["tasks"]:
                                    task.update(est_duration_min=10, duration_source="given")
                path = Path(folder) / "instances.json"
                path.write_text(json.dumps(bundle), encoding="utf-8")
                with self.assertRaises(AssertionError):
                    module.check_handoff(path)

    def test_shared_cases_are_usable_with_lookup_and_taxonomy_inputs(self):
        import sys
        path = ROOT / "scripts/data/build_preliminary_handoff.py"
        self.assertTrue(path.exists(), "Missing shared Preliminary instance builder")
        spec = importlib.util.spec_from_file_location("preliminary_handoff", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.path.insert(0, str(ROOT / "codebase"))
        from planning import draft_schedule, input_issues, validate_plan
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "instances.json"
            module.build_handoff(ROOT, output)
            bundle = json.loads(output.read_text())
        self.assertEqual(bundle["data_kind"], "synthetic")
        self.assertEqual(len(bundle["cases"]), 3)
        with (ROOT / "data/reference/ward_task_duration.csv").open() as stream:
            reference = {r["task_type"]: r for r in csv.DictReader(stream)}
        for case in bundle["cases"]:
            instance = case["instance"]
            self.assertFalse(input_issues(instance), case["id"])
            self.assertTrue(validate_plan(instance, draft_schedule(instance))["valid"], case["id"])
            for patient in instance["patients"]:
                for field in ["acuity_score", "adl_dependency", "care_category", "isolation_precaution"]:
                    self.assertIn(field, patient)
            expected = {t["task_id"]: t for t in instance["tasks"]}
            for task in case["l3_input"]["tasks"]:
                if "est_duration_min" in task:
                    self.assertEqual(task, expected[task["task_id"]])
            self.assertEqual(case["l3_input"]["patients"], instance["patients"])
            for task in instance["tasks"]:
                if task["duration_source"].startswith("lookup:"):
                    import math
                    self.assertEqual(task["est_duration_min"], math.ceil(float(
                        reference[task["task_type"]]["mean_duration_min"]
                    )))
        absent = bundle["cases"][-1]
        self.assertNotIn(absent["absent_nurse_id"], [n["nurse_id"] for n in absent["instance"]["nurses"]])

    def test_handoff_checker_rejects_changed_l3_task_or_patient(self):
        import copy
        spec = importlib.util.spec_from_file_location(
            "preliminary_checker", ROOT / "scripts/data/check_preliminary_handoff.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = json.loads((ROOT / "data/preliminary/instances.json").read_text())
        for change in ["drop_task", "move_patient", "change_acuity"]:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                bundle = copy.deepcopy(original)
                partial = bundle["cases"][1]["l3_input"]
                if change == "drop_task":
                    partial["tasks"].pop()
                elif change == "move_patient":
                    partial["tasks"][1]["patient_id"] = "P6"
                else:
                    partial["patients"][0]["acuity_score"] = 99
                path = Path(folder) / "instances.json"
                path.write_text(json.dumps(bundle))
                with self.assertRaisesRegex(AssertionError, "L3"):
                    module.check_handoff(path)


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "preliminary_eda", ROOT / "scripts/eda/run_eda.py"
        )
        cls.eda = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.eda)

    def test_hour_bins_split_minutes_instead_of_using_episode_start(self):
        import pandas as pd
        segments = pd.DataFrame([
            {"task_start_min_from_date": 655, "task_end_min_from_date": 665},
            {"task_start_min_from_date": 1435, "task_end_min_from_date": 1445},
        ])
        self.assertTrue(hasattr(self.eda, "hourly_minutes"))
        hours = self.eda.hourly_minutes(segments)
        self.assertEqual(hours[10], 5)
        self.assertEqual(hours[11], 5)
        self.assertEqual(hours[23], 5)
        self.assertEqual(hours[0], 5)
        self.assertEqual(sum(hours), 20)

    def test_activity_mean_uses_only_training_staff_even_for_unseen_label(self):
        import pandas as pd
        rows = []
        for staff, values in [("A", [2, 2, 14]), ("B", [5, 5, 20])]:
            for label, duration in zip(["common", "common", staff], values):
                rows.append({"episode_id": len(rows), "staff_id": staff, "task_name": label,
                             "task_category": "one", "nurseflow_task_type": "one",
                             "actual_duration_min": duration})
        _, predictions = self.eda.run_l3_predictability_gate(pd.DataFrame(rows))
        # A's unknown label falls back to B's overall mean and vice versa.
        self.assertEqual(predictions["activity_mean"].tolist(), [5, 5, 10, 2, 2, 6])

    def test_eda_rejects_stale_feature_lineage_before_evaluation(self):
        import pandas as pd
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            for name in ["zenodo_tasks_en.csv", "zenodo_task_episodes_en.csv",
                         "l3_activity_features.csv", "zenodo_translation_glossary.json"]:
                shutil.copy(ROOT / "data/processed" / name, path / name)
            features = pd.read_csv(path / "l3_activity_features.csv")
            features.loc[0, "source_excel_rows"] = "[999999]"
            features.to_csv(path / "l3_activity_features.csv", index=False)
            with self.assertRaisesRegex(ValueError, "Feature rows"):
                self.eda.run_eda(path, path / "figures", path / "report.md", path / "summary.json")

    def test_cv_uses_disjoint_staff_and_only_preplanning_features(self):
        import pandas as pd
        rows = []
        for group in range(6):
            for task, duration in [("A", 5), ("B", 20)]:
                rows.append({
                    "episode_id": f"{group}-{task}", "staff_id": f"S{group}",
                    "nurseflow_task_type": task, "task_name": task,
                    "task_category": "Category", "actual_duration_min": duration,
                    "patient_id": "UNLINKED", "episode_end_min_from_date": 9999,
                })
        result, predictions = self.eda.run_l3_predictability_gate(pd.DataFrame(rows))
        self.assertEqual(result["split_method"], "GroupKFold(staff_id)")
        for fold in result["folds"]:
            self.assertTrue(set(fold["train_groups"]).isdisjoint(fold["test_groups"]))
        self.assertEqual(len(predictions), 12)
        self.assertEqual(predictions.episode_id.nunique(), 12)
        self.assertNotIn("patient_id", result["feature_columns"])
        self.assertNotIn("staff_id", result["feature_columns"])
        self.assertNotIn("episode_end_min_from_date", result["feature_columns"])
        self.assertEqual(result["models"]["task_type_median"]["mae_min"], 0)
        self.assertEqual(result["best_mae_method"], "task_type_median")


if __name__ == "__main__":
    unittest.main()
