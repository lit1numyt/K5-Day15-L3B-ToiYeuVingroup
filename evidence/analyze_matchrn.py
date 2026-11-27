"""EDA stdlib; raw files ở thư mục cache ngoài repo. Chỉ xuất số tổng hợp/5 trích mẫu."""
import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://zenodo.org/records/15248072/files/"
FILES = {
    "Nurse_shift_staffing_workloadMatchRN_2018.csv": "0725f8a99c3c7b4712ca6bab38923dbf",
    "Nurse_shift_staffing_workloadMatchRN_2018_Codebook.xlsx": "212696ce01a3c52951e06d4d080292be",
    "Nurse_shift_staffing_workload_MatchRN_Readme.rtf": "f6452947183b173ed89bd3789585c849",
}
COLUMNS = {"shiftlength":"hours", "C2.6":"minutes", "C2.9":"patients per respondent",
           "patients":"patients on unit", "RNs":"RN count", "other":"other nursing staff count",
           "C3.4":"NASA-TLX temporal demand 1–20"}


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) and value >= 0 else None
    except (TypeError, ValueError):
        return None


def overtime_summary(rows):
    values = [number(r.get("C2.6")) for r in rows]
    valid = [v for v in values if v is not None]
    return {"valid_n":len(valid), "at_least_30_min":sum(v >= 30 for v in valid),
            "missing_or_invalid":len(values)-len(valid)}


def analyze(cache):
    hashes = {}
    for name, expected in FILES.items():
        path = cache / name
        if not path.exists():
            with urlopen(BASE + name, timeout=30) as response:
                path.write_bytes(response.read())
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError("Source version changed: checksum khác metadata " + name)
        hashes[name] = digest
    with (cache / next(iter(FILES))).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        columns = reader.fieldnames
    summary = {"source":"https://zenodo.org/records/15248072", "version":"1.0.0",
               "retrieved":"2026-11-27", "rows":len(rows), "columns":len(columns),
               "md5":hashes, "overtime":overtime_summary(rows), "numeric":{},
               "exact_duplicate_rows":len(rows)-len({tuple(r.values()) for r in rows})}
    for col, unit in COLUMNS.items():
        values = [number(r[col]) for r in rows]
        valid = [v for v in values if v is not None]
        summary["numeric"][col] = {"unit":unit, "valid_n":len(valid),
                                   "missing_or_invalid":len(rows)-len(valid),
                                   "min":min(valid), "median":statistics.median(valid), "max":max(valid)}
    # Chọn trước: 5 bộ staffing khác nhau đầu tiên có các số đếm hợp lệ.
    # Không xuất age, ID, HospID, timestamp hoặc toàn bản ghi cá nhân.
    examples, seen = [], set()
    for index, row in enumerate(rows, start=1):
        values = tuple(number(row[c]) for c in ["shiftlength","patients","RNs","other"])
        if (None in values or min(values[:3]) <= 0 or values in seen
                or any(v != int(v) for v in values[1:])):
            continue
        seen.add(values)
        examples.append({"source_data_row":index, "shift_hours":values[0],
                         "unit_patient_count":int(values[1]), "rn_count":int(values[2]),
                         "other_staff_count":int(values[3])})
        if len(examples) == 5:
            break
    summary["staffing_excerpts"] = examples
    target = ROOT / "evidence" / "matchrn-summary.json"
    target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True,help="thư mục raw ngoài repo")
    args = parser.parse_args()
    if args.cache.resolve().is_relative_to(ROOT):
        parser.error("raw cache phải nằm ngoài repo")
    args.cache.mkdir(parents=True,exist_ok=True)
    analyze(args.cache)
