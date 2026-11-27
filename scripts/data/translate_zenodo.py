"""Translate and normalize Zenodo 20754938 (Japanese OR nursing time-and-motion data) to English.

Reads raw Excel (xl/worksheets/sheet1.xml + xl/sharedStrings.xml via Python stdlib so no
external xlsx dependency is required), translates Japanese column headers and categorical
values into English, converts Excel serial dates/time fractions into ISO dates, timestamps,
and durations in minutes, and maps tasks to NurseFlow task_type taxonomy.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

EXCEL_EPOCH = dt.date(1899, 12, 30)

COLUMN_MAP = {
    "日付": "date",
    "職員No": "staff_id",
    "作業開始時間": "task_start_raw",
    "作業終了時間": "task_end_raw",
    "時間帯": "hour_slot_ja",
    "作業時間": "task_duration_days",
    "看護非看護名": "nursing_class",
    "カテゴリ名": "task_category",
    "調査項目名称": "task_name",
    "シフト名称": "shift_code_raw",
    "開始時刻": "shift_start_raw",
    "終了時刻": "shift_end_raw",
    "超過勤務": "overtime_status",
}

NURSING_CLASS_MAP = {
    "看護": "Nursing",
    "非看護": "Non-Nursing",
    "休憩": "Break",
}

CATEGORY_MAP = {
    "その他": "Other",
    "休憩": "Break",
    "手術関連業務（看）": "Surgery-Related Work (Nursing)",
    "手術関連業務（非看護）": "Surgery-Related Work (Non-Nursing)",
    "教育": "Education & Training",
    "書類業務": "Documentation",
    "洗浄滅菌業務": "Cleaning & Sterilization",
    "準備（看）": "Preparation (Nursing)",
    "準備（非看護）": "Preparation (Non-Nursing)",
    "片付け": "Cleanup & Tidying",
    "物品管理": "Supply & Inventory Management",
    "管理業務": "Administrative & Management",
    "部署応援": "Interdepartmental Support",
}

TASK_NAME_MAP = {
    "その他の物品管理": "Other Supplies Management",
    "オペ台作り": "Operating Table Setup",
    "スタッフ指導（指導をする側）": "Staff Mentoring (Preceptor)",
    "スタッフ指導（指導を受ける側）": "Staff Training (Trainee)",
    "テーブル広げ作業": "Sterile Table Draping & Setup",
    "メッセンジャー業務": "Messenger / Courier Duties",
    "メーカー対応": "Vendor / Manufacturer Coordination",
    "リーダー業務": "Shift Leader Duties",
    "他部署応援": "Other Department Support",
    "伝票整理": "Slip & Form Processing",
    "使用後の手術器材片付け": "Post-Use Surgical Equipment Cleanup",
    "勉強会・伝達会": "Study Session / Briefing",
    "勤務時間中の食事・休憩・休息": "Meal / Break / Rest During Shift",
    "器械の洗浄、組み立て、滅菌": "Instrument Cleaning, Assembly & Sterilization",
    "器械出し看護": "Scrub Nursing",
    "器械（鋼製小物）の物品管理": "Surgical Instrument Inventory Management",
    "報告要件": "Reporting Duties",
    "外回り看護": "Circulating Nursing",
    "委員会会議": "Committee Meeting",
    "委員会業務": "Committee Duties",
    "患者搬送（外回り看護）": "Patient Transport (Circulating Nursing)",
    "患者搬送（応援）": "Patient Transport (Support)",
    "手指消毒チェック": "Hand Hygiene / Scrub Check",
    "手術介助見守り・補佐": "Surgical Assistance Observation / Support",
    "手術室入退部前後の申し送り": "Pre/Post-OR Entry/Exit Handover",
    "手術室内の物品管理": "In-OR Supplies Management",
    "手術室看護師間引継ぎ": "OR Nurse Handover",
    "担当患者情報収集": "Assigned Patient Information Gathering",
    "未使用品片付け（その他）": "Unused Supplies Cleanup (Other)",
    "未使用品片付け（材料、器械）": "Unused Supplies Cleanup (Materials & Instruments)",
    "材料・器械集め": "Gathering Materials & Instruments",
    "清掃、部屋片づけ": "Cleaning & Room Tidying",
    "管理者の業務": "Manager / Supervisor Duties",
    "薬剤準備": "Medication Preparation",
    "術前外来": "Preoperative Outpatient Clinic",
    "術前情報収集": "Preoperative Information Gathering",
    "術前訪問": "Preoperative Visit",
    "術後訪問": "Postoperative Visit",
    "術衣やごみの回収・補充": "Surgical Gown & Waste Collection / Restocking",
    "診療材料の物品管理": "Medical Supplies Inventory Management",
    "部屋作り（当日）": "OR Room Setup (Same-Day)",
    "部屋作り（翌日）": "OR Room Setup (Next-Day)",
    "部署内カンファレンス": "Department Conference",
    "部署内係業務": "Department Committee / Role Duties",
    "院内研修": "In-Hospital Training",
    "項目外業務": "Unlisted / Miscellaneous Tasks",
}

SHIFT_CODE_MAP = {
    "10": "Shift-10",
    "9": "Shift-9",
    "F7": "Shift-F7",
    "OC": "On-Call",
    "≪,≫": "Split-Shift",
    "○1": "Day-Regular-1",
    "○2": "Day-Regular-2",
    "○3": "Day-Regular-3",
    "○4": "Day-Regular-4",
    "●": "Day-Filled",
    "〇": "Day-Circle",
    "ネ/": "Night-Shift",
    "遅A": "Late-A",
    "遅B": "Late-B",
    "遅D": "Late-D",
    "遅F": "Late-F",
    "遅H": "Late-H",
}

OVERTIME_MAP = {
    "": "Regular",
    "定時外": "Overtime",
}

# Alignment to NurseFlow feature-spec task_type taxonomy
NURSEFLOW_TASK_TYPE_MAP = {
    "Scrub Nursing": "procedure_care",
    "Circulating Nursing": "procedure_care",
    "Surgical Assistance Observation / Support": "procedure_care",
    "Preoperative Visit": "assessment",
    "Postoperative Visit": "assessment",
    "Preoperative Outpatient Clinic": "assessment",
    "Assigned Patient Information Gathering": "documentation",
    "Preoperative Information Gathering": "documentation",
    "Slip & Form Processing": "documentation",
    "Reporting Duties": "documentation",
    "OR Nurse Handover": "handover",
    "Pre/Post-OR Entry/Exit Handover": "handover",
    "Department Conference": "handover",
    "Medication Preparation": "med_admin",
    "Patient Transport (Circulating Nursing)": "mobilization",
    "Patient Transport (Support)": "mobilization",
    "Hand Hygiene / Scrub Check": "safety_prep",
    "OR Room Setup (Same-Day)": "prep_setup",
    "OR Room Setup (Next-Day)": "prep_setup",
    "Operating Table Setup": "prep_setup",
    "Sterile Table Draping & Setup": "prep_setup",
    "Gathering Materials & Instruments": "prep_setup",
    "Post-Use Surgical Equipment Cleanup": "cleanup_sterilization",
    "Instrument Cleaning, Assembly & Sterilization": "cleanup_sterilization",
    "Unused Supplies Cleanup (Materials & Instruments)": "cleanup_sterilization",
    "Unused Supplies Cleanup (Other)": "cleanup_sterilization",
    "Cleaning & Room Tidying": "cleanup_sterilization",
    "Surgical Gown & Waste Collection / Restocking": "cleanup_sterilization",
    "Surgical Instrument Inventory Management": "supply_management",
    "Medical Supplies Inventory Management": "supply_management",
    "In-OR Supplies Management": "supply_management",
    "Other Supplies Management": "supply_management",
    "Meal / Break / Rest During Shift": "break",
    "Shift Leader Duties": "coordination",
    "Manager / Supervisor Duties": "coordination",
    "Department Committee / Role Duties": "coordination",
    "Committee Meeting": "coordination",
    "Committee Duties": "coordination",
    "Staff Mentoring (Preceptor)": "education",
    "Staff Training (Trainee)": "education",
    "Study Session / Briefing": "education",
    "In-Hospital Training": "education",
    "Messenger / Courier Duties": "support",
    "Vendor / Manufacturer Coordination": "support",
    "Other Department Support": "support",
    "Unlisted / Miscellaneous Tasks": "other",
}


def excel_serial_to_date(serial_str: str) -> str:
    """Convert an Excel serial date number string to YYYY-MM-DD."""
    days = int(float(serial_str))
    return (EXCEL_EPOCH + dt.timedelta(days=days)).isoformat()


def excel_fraction_to_hhmmss(val: str) -> tuple[str, float | None]:
    """Convert Excel day-fraction (can exceed 1.0 after midnight) to HH:MM:SS and minutes from 00:00."""
    if not val:
        return "", None
    frac = float(val)
    total_seconds = round(frac * 86400)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}", round(frac * 1440.0, 2)


def parse_hour_slot(hour_slot_ja: str) -> int:
    """Convert '11時' -> 11."""
    return int(hour_slot_ja.replace("時", "").strip())


def read_xlsx_rows(xlsx_path: Path) -> list[list[str]]:
    """Read first worksheet of an .xlsx file into a list of cell lists (columns A..M)."""
    ns_main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ns = {"m": ns_main}
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        shared_strings = ["".join(si.itertext()) for si in ss_root.findall(f"{{{ns_main}}}si")]
        sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        xml_rows = sheet_root.findall(".//m:sheetData/m:row", ns)

    parsed_rows: list[list[str]] = []
    for r in xml_rows:
        row_cells = [""] * 13
        for c in r.findall("m:c", ns):
            ref = c.attrib.get("r", "")
            col_letters = "".join(ch for ch in ref if ch.isalpha())
            col_idx = ord(col_letters) - ord("A")
            v = c.find("m:v", ns)
            if v is None or v.text is None:
                val = ""
            elif c.attrib.get("t") == "s":
                val = shared_strings[int(v.text)]
            else:
                val = v.text
            if 0 <= col_idx < 13:
                row_cells[col_idx] = val
        parsed_rows.append(row_cells)
    return parsed_rows


def translate_dataset(input_xlsx: Path, output_csv: Path, vocab_json: Path, episodes_csv: Path | None = None) -> dict:
    """Translate Zenodo 20754938 Data.xlsx to English CSV, merge contiguous episodes, and export glossary."""
    raw_rows = read_xlsx_rows(input_xlsx)
    headers_ja = raw_rows[0]
    expected_ja = list(COLUMN_MAP.keys())
    if headers_ja != expected_ja:
        raise ValueError(f"Unexpected headers: {headers_ja} != {expected_ja}")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    vocab_json.parent.mkdir(parents=True, exist_ok=True)
    if episodes_csv is None:
        episodes_csv = output_csv.with_name("zenodo_task_episodes_en.csv")

    out_fields = [
        "record_id",
        "episode_id",
        "date",
        "day_of_week",
        "staff_id",
        "task_start_hhmmss",
        "task_end_hhmmss",
        "task_start_min_of_day",
        "task_end_min_of_day",
        "hour_of_day",
        "hour_slot_en",
        "actual_duration_min",
        "nursing_class",
        "task_category",
        "task_name",
        "nurseflow_task_type",
        "prep_required",
        "shift_code",
        "shift_code_raw",
        "shift_start_hhmmss",
        "shift_end_hhmmss",
        "shift_length_min",
        "is_overtime",
        "overtime_status",
        "nursing_class_ja",
        "task_category_ja",
        "task_name_ja",
    ]

    unmapped = {"nursing_class": set(), "task_category": set(), "task_name": set(), "shift_code": set()}
    parsed_records: list[dict] = []

    for idx, row in enumerate(raw_rows[1:], start=1):
        (
            date_raw,
            staff_raw,
            t_start_raw,
            t_end_raw,
            hour_ja,
            dur_raw,
            n_class_ja,
            cat_ja,
            task_ja,
            shift_ja,
            s_start_raw,
            s_end_raw,
            ot_ja,
        ) = row

        if n_class_ja not in NURSING_CLASS_MAP:
            unmapped["nursing_class"].add(n_class_ja)
        if cat_ja not in CATEGORY_MAP:
            unmapped["task_category"].add(cat_ja)
        if task_ja not in TASK_NAME_MAP:
            unmapped["task_name"].add(task_ja)
        if shift_ja not in SHIFT_CODE_MAP:
            unmapped["shift_code"].add(shift_ja)

        date_iso = excel_serial_to_date(date_raw)
        dow = dt.date.fromisoformat(date_iso).strftime("%A")
        t_start_str, t_start_min = excel_fraction_to_hhmmss(t_start_raw)
        t_end_str, t_end_min = excel_fraction_to_hhmmss(t_end_raw)
        hour_int = parse_hour_slot(hour_ja)
        dur_min = round(float(dur_raw) * 1440.0, 2)

        s_start_str, s_start_min = excel_fraction_to_hhmmss(s_start_raw)
        s_end_str, s_end_min = excel_fraction_to_hhmmss(s_end_raw)
        if s_start_min is not None and s_end_min is not None:
            shift_len_min = round(s_end_min - s_start_min, 2)
            if shift_len_min < 0:
                shift_len_min = round(shift_len_min + 1440.0, 2)
        else:
            shift_len_min = ""

        n_class_en = NURSING_CLASS_MAP.get(n_class_ja, n_class_ja)
        cat_en = CATEGORY_MAP.get(cat_ja, cat_ja)
        task_en = TASK_NAME_MAP.get(task_ja, task_ja)
        nf_type = NURSEFLOW_TASK_TYPE_MAP.get(task_en, "other")
        prep_req = 1 if nf_type in {"prep_setup", "med_admin", "safety_prep"} else 0
        shift_en = SHIFT_CODE_MAP.get(shift_ja, shift_ja)
        ot_en = OVERTIME_MAP.get(ot_ja, ot_ja)
        is_ot = 1 if ot_en == "Overtime" else 0

        parsed_records.append(
            {
                "record_id": f"ZND-{idx:05d}",
                "date": date_iso,
                "day_of_week": dow,
                "staff_id": f"OR_STAFF_{int(float(staff_raw)):02d}",
                "task_start_hhmmss": t_start_str,
                "task_end_hhmmss": t_end_str,
                "task_start_min_of_day": t_start_min,
                "task_end_min_of_day": t_end_min,
                "hour_of_day": hour_int,
                "hour_slot_en": f"{hour_int:02d}:00-{hour_int:02d}:59",
                "actual_duration_min": dur_min,
                "nursing_class": n_class_en,
                "task_category": cat_en,
                "task_name": task_en,
                "nurseflow_task_type": nf_type,
                "prep_required": prep_req,
                "shift_code": shift_en,
                "shift_code_raw": shift_ja,
                "shift_start_hhmmss": s_start_str,
                "shift_end_hhmmss": s_end_str,
                "shift_length_min": shift_len_min,
                "is_overtime": is_ot,
                "overtime_status": ot_en,
                "nursing_class_ja": n_class_ja,
                "task_category_ja": cat_ja,
                "task_name_ja": task_ja,
            }
        )

    if any(unmapped.values()):
        raise ValueError(f"Unmapped Japanese terms detected: {unmapped}")

    # Group consecutive 10-minute observation blocks of the same task into continuous task episodes
    parsed_records.sort(
        key=lambda r: (r["staff_id"], r["date"], r["shift_code_raw"], r["task_start_min_of_day"] or 0.0)
    )
    episodes: list[dict] = []
    ep_num = 0
    prev: dict | None = None
    for rec in parsed_records:
        is_same_ep = (
            prev is not None
            and rec["staff_id"] == prev["staff_id"]
            and rec["date"] == prev["date"]
            and rec["shift_code_raw"] == prev["shift_code_raw"]
            and rec["task_name"] == prev["task_name"]
            and abs((rec["task_start_min_of_day"] or 0.0) - (prev["task_end_min_of_day"] or 0.0)) <= 0.1
        )
        if not is_same_ep:
            ep_num += 1
            ep_id = f"ZEP-{ep_num:04d}"
            episodes.append(
                {
                    "episode_id": ep_id,
                    "date": rec["date"],
                    "day_of_week": rec["day_of_week"],
                    "staff_id": rec["staff_id"],
                    "shift_code": rec["shift_code"],
                    "shift_start_hhmmss": rec["shift_start_hhmmss"],
                    "shift_end_hhmmss": rec["shift_end_hhmmss"],
                    "shift_length_min": rec["shift_length_min"],
                    "episode_start_hhmmss": rec["task_start_hhmmss"],
                    "episode_end_hhmmss": rec["task_end_hhmmss"],
                    "episode_start_min_of_day": rec["task_start_min_of_day"],
                    "episode_end_min_of_day": rec["task_end_min_of_day"],
                    "hour_of_day": rec["hour_of_day"],
                    "segment_count": 1,
                    "episode_duration_min": rec["actual_duration_min"],
                    "nursing_class": rec["nursing_class"],
                    "task_category": rec["task_category"],
                    "task_name": rec["task_name"],
                    "nurseflow_task_type": rec["nurseflow_task_type"],
                    "prep_required": rec["prep_required"],
                    "is_overtime": rec["is_overtime"],
                }
            )
        else:
            ep = episodes[-1]
            ep["episode_end_hhmmss"] = rec["task_end_hhmmss"]
            ep["episode_end_min_of_day"] = rec["task_end_min_of_day"]
            ep["segment_count"] += 1
            ep["episode_duration_min"] = round(ep["episode_duration_min"] + rec["actual_duration_min"], 2)
            ep["is_overtime"] = max(ep["is_overtime"], rec["is_overtime"])
        rec["episode_id"] = f"ZEP-{ep_num:04d}"
        prev = rec

    parsed_records.sort(key=lambda r: r["record_id"])
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(parsed_records)

    ep_fields = list(episodes[0].keys())
    with open(episodes_csv, "w", newline="", encoding="utf-8") as ef:
        writer = csv.DictWriter(ef, fieldnames=ep_fields)
        writer.writeheader()
        writer.writerows(episodes)

    glossary = {
        "source": "Zenodo 20754938 (10.5281/zenodo.20754938)",
        "records_translated": len(parsed_records),
        "episodes_merged": len(episodes),
        "columns": COLUMN_MAP,
        "nursing_class": NURSING_CLASS_MAP,
        "task_category": CATEGORY_MAP,
        "task_name": TASK_NAME_MAP,
        "shift_code": SHIFT_CODE_MAP,
        "overtime_status": OVERTIME_MAP,
        "nurseflow_task_type": NURSEFLOW_TASK_TYPE_MAP,
    }
    with open(vocab_json, "w", encoding="utf-8") as vf:
        json.dump(glossary, vf, ensure_ascii=False, indent=2)

    return {
        "rows": len(parsed_records),
        "episodes": len(episodes),
        "output_csv": str(output_csv),
        "episodes_csv": str(episodes_csv),
        "vocab_json": str(vocab_json),
    }


def main() -> None:
    default_input = Path("data/zenodo_20754938/Data.xlsx")
    parser = argparse.ArgumentParser(description="Translate Zenodo 20754938 Data.xlsx to English CSV.")
    parser.add_argument("--input", type=Path, default=default_input)
    parser.add_argument("--output", type=Path, default=Path("data/processed/zenodo_tasks_en.csv"))
    parser.add_argument("--vocab", type=Path, default=Path("data/processed/zenodo_translation_glossary.json"))
    args = parser.parse_args()
    res = translate_dataset(args.input, args.output, args.vocab)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
