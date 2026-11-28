"""Đối chiếu số liệu MIMIC-IV Demo 2.2 cho B16–B18. Chỉ in số tổng hợp."""
import csv
import gzip
import io
from collections import Counter
from urllib.request import urlopen


def rows(dataset, table):
    url = f"https://physionet.org/files/{dataset}/2.2/{table}.csv.gz"
    with urlopen(url, timeout=60) as response:
        with gzip.GzipFile(fileobj=response) as compressed:
            yield from csv.DictReader(io.TextIOWrapper(compressed, encoding="utf-8-sig"))


def main():
    clinical = "mimic-iv-demo"
    ed = "mimic-iv-ed-demo"
    patients = {r["subject_id"] for r in rows(clinical, "hosp/patients")}
    stays = list(rows(ed, "ed/edstays"))
    ed_patients = {r["subject_id"] for r in stays}
    print("B18 | patients Clinical, lượt ED, bệnh nhân ED, bệnh nhân chung, lượt có hadm_id:",
          len(patients), len(stays), len(ed_patients), len(ed_patients & patients),
          sum(bool(r["hadm_id"]) for r in stays))
    acuity = Counter(r["acuity"] or "thiếu" for r in rows(ed, "ed/triage"))
    print("Triage | số lượt theo acuity:", dict(sorted(acuity.items())))

    medication = rows(clinical, "hosp/emar")
    first = next(medication)
    print("B16 | số bản ghi eMAR:", 1 + sum(1 for _ in medication))
    print("B16 | các cột thời điểm:", [k for k in first if k.endswith("time")])

    items = Counter(r["itemid"] for r in rows(clinical, "icu/procedureevents"))
    label = next(r["label"] for r in rows(clinical, "icu/d_items") if r["itemid"] == "225792")
    print("B17 | số sự kiện, nhãn và số dòng item 225792:", sum(items.values()), label, items["225792"])


if __name__ == "__main__":
    main()
