"""In bản đồ taxonomy L4 từ model ĐÃ SHIP (không train lại).

Dùng `classify_patient` nên phản ánh đúng hành vi runtime (model nếu có sklearn, không thì
fallback rule — kết quả giống nhau). Hữu ích để nhóm thảo luận / dán vào slide.

Chạy:  python scripts/l4/show_taxonomy.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))
from baseline import classify_patient  # noqa: E402

META = json.loads((ROOT / "codebase/L4/taxonomy_meta.json").read_text(encoding="utf-8"))
ACUITIES, ADLS = range(1, 6), range(1, 5)


def tier(acuity, adl, iso):
    return classify_patient({"acuity_score": acuity, "adl_dependency": adl,
                             "isolation_precaution": bool(iso)})["tier"]


def main():
    print("=== L4 Taxonomy bệnh nhân (model KMeans đã ship) ===")
    print(f"k={META['k']} | điểm cắt tier={META['tier_score_ranges']} | "
          f"fixture {META['fixture_agreement']}")
    print(f"silhouette theo k={META['silhouette_by_k']} (chọn k theo low/med/high)")
    print(f"build: sklearn {META['sklearn_version']} / numpy {META['numpy_version']} "
          f"/ py {META['python_version']} | seed={META['seed']}")
    print("workload_weight = acuity+adl+isolation (điểm tương đối, KHÔNG phải phút)\n")

    for iso in (0, 1):
        print(f"Bản đồ tier (isolation={iso})   [ô = Tier(điểm)]")
        print("  adl\\acuity " + "".join(f"{a:>8}" for a in ACUITIES))
        for d in reversed(list(ADLS)):
            cells = "".join(f"  T{tier(a, d, iso)}({a + d + iso:>2})" for a in ACUITIES)
            print(f"      {d:>4}  {cells}")
        print()


if __name__ == "__main__":
    main()
