"""Huấn luyện taxonomy bệnh nhân L4 bằng KMeans (unsupervised) và XUẤT artifact shipped.

Luồng:
  1. Đọc population synthetic (scripts/l4/make_patient_population.py).
  2. Cluster trên 1 chiều: workload_score = acuity + adl + isolation. Clustering 2D (acuity,adl)
     cho vùng Voronoi KHÔNG đơn điệu (bệnh nhân nhẹ hơn có thể rơi tier cao hơn — vô lý); taxonomy
     workload BẮT BUỘC đơn điệu. KMeans 1D tìm điểm cắt tự nhiên trong phân bố điểm (kiểu Jenks),
     đơn điệu theo cấu trúc, và gộp isolation an toàn (không bị StandardScaler thổi phồng binary).
  3. KMeans(k=3) — 3 tier low/med/high theo quy ước lâm sàng; silhouette k=2..6 báo cáo chẩn đoán.
  4. Sắp cluster -> tier ordinal theo centroid điểm tăng dần.
  5. Sanity-assert: tier đơn điệu theo workload_score trên toàn lưới; đối chiếu 6 fixture.
  6. Xuất: codebase/L4/taxonomy_model.pkl, taxonomy_meta.json, docs/figures/l4_patient_clusters.png.

Pickle phụ thuộc phiên bản sklearn/numpy -> ghi phiên bản vào meta; runtime có rule fallback.
Chạy bằng Python có sklearn:  python scripts/l4/train_taxonomy.py
"""
import hashlib
import json
import pickle
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[2]
POP = ROOT / "data/synthetic/patient_population.csv"
MODEL_OUT = ROOT / "codebase/L4/taxonomy_model.pkl"
META_OUT = ROOT / "codebase/L4/taxonomy_meta.json"
FIG_OUT = ROOT / "docs/figures/l4_patient_clusters.png"

SCORE_PARTS = ["acuity_score", "adl_dependency", "isolation_precaution"]
SEED = 42
SELECT_K = 3  # low/med/high theo quy ước lâm sàng
K_RANGE = range(2, 7)

# 6 bệnh nhân fixture (data/preliminary/instances.json): acuity, adl, isolation, rule_tier.
# Rule cũ: weight = acuity+adl+isolation; <=3 -> 1, <=6 -> 2, else 3.
FIXTURES = [(1, 1, 0, 1), (3, 2, 0, 2), (5, 4, 1, 3),
            (1, 1, 0, 1), (3, 2, 0, 2), (5, 4, 0, 3)]


def load_scores():
    rows = np.genfromtxt(POP, delimiter=",", names=True, dtype=None, encoding="utf-8")
    score = sum(rows[p].astype(float) for p in SCORE_PARTS)
    return score.reshape(-1, 1)


def silhouette_by_k(scores):
    out = {}
    for k in K_RANGE:
        labels = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit_predict(scores)
        out[k] = float(silhouette_score(scores, labels))
    return out


def order_clusters(scores, labels, k):
    """cluster id -> tier ordinal (1..k) theo centroid điểm tăng dần."""
    centroid = {c: float(scores[labels == c].mean()) for c in range(k)}
    ordered = sorted(centroid, key=centroid.get)
    return {int(c): rank + 1 for rank, c in enumerate(ordered)}, centroid


def main():
    if not POP.exists():
        sys.exit("Thiếu population; chạy scripts/l4/make_patient_population.py trước.")
    scores = load_scores()
    sil = silhouette_by_k(scores)

    model = KMeans(n_clusters=SELECT_K, random_state=SEED, n_init=10)
    labels = model.fit_predict(scores)
    cluster_to_tier, centroid = order_clusters(scores, labels, SELECT_K)

    def tier_of(acuity, adl, iso):
        return cluster_to_tier[int(model.predict([[acuity + adl + iso]])[0])]

    # Sanity 1: đơn điệu theo workload_score trên toàn lưới acuity×adl×isolation.
    grid = {(a, d, i): tier_of(a, d, i)
            for a in range(1, 6) for d in range(1, 5) for i in (0, 1)}
    for (a, d, i), t in grid.items():
        for (a2, d2, i2), t2 in grid.items():
            if (a2 + d2 + i2) >= (a + d + i):
                assert t2 >= t, f"Không đơn điệu: {(a, d, i)}->{t} vs {(a2, d2, i2)}->{t2}"

    # Sanity 2: đối chiếu 6 fixture với rule cũ.
    fixture_report = [{"acuity": a, "adl": d, "isolation": i,
                       "rule_tier": rt, "model_tier": tier_of(a, d, i)}
                      for a, d, i, rt in FIXTURES]
    agree = sum(r["rule_tier"] == r["model_tier"] for r in fixture_report)
    assert agree == len(FIXTURES), f"Fixture không khớp rule: {fixture_report}"

    # Ranh giới điểm giữa các tier (để runtime fallback khớp model & cho figure).
    tier_scores = {}
    for s in range(2, 11):
        tier_scores.setdefault(cluster_to_tier[int(model.predict([[s]])[0])], []).append(s)
    tier_ranges = {str(t): [min(v), max(v)] for t, v in sorted(tier_scores.items())}

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_OUT.open("wb") as fh:
        pickle.dump(model, fh)
    meta = {
        "model_file": MODEL_OUT.name,
        "cluster_feature": "workload_score = acuity_score + adl_dependency + isolation_precaution",
        "workload_weight_formula": "acuity_score + adl_dependency + isolation_precaution",
        "k": SELECT_K,
        "k_selection": "clinical_low_med_high; silhouette báo cáo làm chẩn đoán",
        "k_silhouette_max": int(max(sil, key=sil.get)),
        "cluster_to_tier": {str(c): t for c, t in cluster_to_tier.items()},
        "cluster_centroid_score": {str(c): round(v, 3) for c, v in centroid.items()},
        "tier_score_ranges": tier_ranges,
        "silhouette_by_k": {str(kk): round(v, 4) for kk, v in sil.items()},
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "seed": SEED,
        "population_file": "data/synthetic/patient_population.csv",
        "population_sha256": hashlib.sha256(POP.read_bytes()).hexdigest(),
        "fixture_report": fixture_report,
        "fixture_agreement": f"{agree}/{len(FIXTURES)}",
        "built_on": date.today().isoformat(),
    }
    META_OUT.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Figure: silhouette theo k + histogram workload_score tô theo tier (điểm cắt tự nhiên).
    tiers = np.array([cluster_to_tier[int(c)] for c in labels])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.plot(list(sil), list(sil.values()), "o-")
    ax1.axvline(SELECT_K, color="crimson", ls="--", lw=1, label=f"chọn k={SELECT_K}")
    ax1.set(xlabel="k", ylabel="silhouette", title="Silhouette theo k (chẩn đoán)")
    ax1.legend()
    bins = np.arange(1.5, 11.5, 1)
    for t in sorted(set(tiers)):
        ax2.hist(scores[tiers == t], bins=bins, alpha=0.7, label=f"tier {t}")
    ax2.set(xlabel="workload_score (acuity+adl+isolation)", ylabel="số bệnh nhân",
            title="Điểm cắt tier do KMeans tìm")
    ax2.legend()
    fig.tight_layout()
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_OUT, dpi=120)

    print(f"k={SELECT_K} (silhouette_max tại k={meta['k_silhouette_max']}) | "
          f"fixture {agree}/{len(FIXTURES)}")
    print(f"tier_score_ranges={tier_ranges} | cluster_to_tier={cluster_to_tier}")
    for r in fixture_report:
        print(f"  a={r['acuity']} d={r['adl']} i={r['isolation']}: "
              f"rule={r['rule_tier']} model={r['model_tier']}")
    print(f"Wrote {MODEL_OUT.name}, {META_OUT.name}, {FIG_OUT.name}")


if __name__ == "__main__":
    main()
