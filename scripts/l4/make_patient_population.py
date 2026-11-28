"""Sinh POPULATION bệnh nhân SYNTHETIC để huấn luyện taxonomy L4 (unsupervised).

QUAN TRỌNG (chống bịa): đây là dữ liệu SYNTHETIC, tạo xác định bằng seed. KHÔNG phải
bệnh nhân thật, KHÔNG phải pain evidence. Mục đích duy nhất: cho KMeans một phân bố mật
độ trên không gian đặc trưng bệnh nhân (acuity × adl × isolation) để *khám phá* ranh giới
tier, thay cho ngưỡng chọn tay. Không có nguồn quan sát patient–workload liên kết
(xem data/reference/preliminary_sources.json: McGill `no_observed_patient_samples`).

Thang ordinal theo fixture kỹ thuật (data/preliminary/instances.json):
  acuity_score ∈ 1..5, adl_dependency ∈ 1..4, isolation_precaution ∈ {0,1}.
Trọng số lấy mẫu nghiêng về acuity/adl thấp (đa số bệnh nhân nhẹ hơn) — giả định synthetic,
ghi rõ ở đây và trong data/DATA_CARD.md; đổi trọng số không đổi tính hợp lệ của phương pháp.

Chỉ dùng thư viện chuẩn. Chạy:  python scripts/l4/make_patient_population.py
"""
import csv
import random
from pathlib import Path

SEED = 42
N = 3000
OUT = Path(__file__).resolve().parents[2] / "data/synthetic/patient_population.csv"

# Phân bố synthetic (ghi lại để tái lập). Trọng số theo mức ordinal.
ACUITY_WEIGHTS = {1: 0.30, 2: 0.25, 3: 0.20, 4: 0.15, 5: 0.10}
ADL_WEIGHTS = {1: 0.35, 2: 0.30, 3: 0.20, 4: 0.15}
ISOLATION_P = 0.15
CARE_CATEGORIES = ["medical"]  # fixture chỉ có 'medical'; cấu trúc sẵn cho loại khác


def _sample(rng, weights):
    values, probs = zip(*weights.items())
    return rng.choices(values, weights=probs, k=1)[0]


def main():
    rng = random.Random(SEED)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["patient_id", "acuity_score", "adl_dependency",
                         "isolation_precaution", "care_category", "data_kind"])
        for i in range(N):
            writer.writerow([
                f"SYN{i:04d}",
                _sample(rng, ACUITY_WEIGHTS),
                _sample(rng, ADL_WEIGHTS),
                int(rng.random() < ISOLATION_P),
                rng.choice(CARE_CATEGORIES),
                "synthetic",
            ])
    print(f"Wrote {N} synthetic patients (seed={SEED}) -> {OUT}")


if __name__ == "__main__":
    main()
