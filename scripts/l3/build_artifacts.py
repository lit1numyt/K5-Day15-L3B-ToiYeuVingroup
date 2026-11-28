"""Xuất artifact model OR được chọn, phân tích độ nhạy workload/nghỉ và biểu đồ L3.

Chạy SAU train_or_experiment.py:  python scripts/l3/build_artifacts.py
Đầu ra: artifacts/l3/or_activity_median_v1.json (+ metadata), artifacts/l3/workload_sensitivity.json,
docs/figures/l3_*.png.

Phân tích độ nhạy là MINH HỌA:
- Phần A: phép tính tất định, không dùng dữ liệu.
- Phần B: ca SYNTHETIC ghép từ episode phòng mổ có dự đoán out-of-fold thật (seed 42).
  Không phải quan sát ca nội trú; giả định các episode độc lập.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "l3"))
from train_or_experiment import (FEATURE_COLUMNS, GROUP_COLUMN, MODELS, SEED,  # noqa: E402
                                 TARGET_COLUMN, build_model, sha256)

ART = ROOT / "artifacts" / "l3"
FIG = ROOT / "docs" / "figures"
# Chọn Ridge: MAE từng task kém median ~1,5 phút nhưng tổng workload ít bị đánh giá thiếu hơn
# nhiều (xem phần B), RMSE/R² ngang GBT, dễ giải thích (hệ số theo hoạt động), rẻ nhất trong nhóm ML.
SELECTED = "ridge"
REFERENCE = "activity_median"
COMPARE = (REFERENCE, "ridge", "gradient_boosting")
SHIFT_MIN = 480
# Mốc nghiên cứu từ evidence/workload-research.md (không phải ngưỡng quá tải lâm sàng phổ quát).
PLANNED_LEVELS = {"390 (Hybrid + buffer 30)": 390, "420 (Hybrid 60)": 420, "450 (nghỉ 30)": 450}
LABELS = {"global_median": "Global median", "task_type_median": "Task-type median",
          "activity_median": "Activity median", "ridge": "Ridge", "random_forest": "Random Forest",
          "gradient_boosting": "Gradient Boosting", "mlp": "MLP"}


def predict_from_json(artifact, rows):
    """Dự đoán chỉ từ JSON hệ số (không cần pickle): intercept + Σ hệ số one-hot, chặn dưới 1 phút."""
    out = []
    for row in rows:
        value = artifact["intercept"]
        for column in artifact["features"]:
            value += artifact["coefficients"][column].get(str(row[column]), 0.0)
        out.append(max(value, artifact["prediction_floor_min"]))
    return np.array(out)


def export_selected(summary):
    df = pd.read_csv(ROOT / "data" / "processed" / "l3_activity_features.csv")
    model = build_model("ridge", df[GROUP_COLUMN].to_numpy())
    model.fit(df[FEATURE_COLUMNS], df[TARGET_COLUMN])
    ohe, ridge = model[0], model[-1]
    coefs, offset = {}, 0
    for column, categories in zip(FEATURE_COLUMNS, ohe.categories_):
        coefs[column] = {str(c): float(ridge.coef_[offset + i]) for i, c in enumerate(categories)}
        offset += len(categories)
    artifact = {
        "model_name": "or_ridge_onehot", "model_version": "1",
        "algorithm": "RidgeCV trên one-hot(%s)" % ", ".join(FEATURE_COLUMNS),
        "alpha": float(ridge.alpha_), "intercept": float(ridge.intercept_), "features": FEATURE_COLUMNS,
        "coefficients": coefs, "prediction_floor_min": 1.0, "unknown_category": "hệ số 0 (bỏ qua cột đó)",
        "fit_on": "toàn bộ 2.192 episode (metric báo cáo là out-of-fold, không phải trên dữ liệu fit)",
    }
    # Bảo đảm JSON tái tạo đúng dự đoán của pipeline sklearn.
    sk = np.maximum(model.predict(df[FEATURE_COLUMNS]), 1.0)
    js = predict_from_json(artifact, df[FEATURE_COLUMNS].to_dict("records"))
    assert np.allclose(sk, js, atol=1e-6), "JSON không khớp sklearn"
    held = summary["overall"]["held_out_staff"]
    later = summary["overall"]["later_time"]
    meta = {
        "model_name": artifact["model_name"], "model_version": "1", "algorithm": artifact["algorithm"],
        "target": "actual_duration_min — phút activity episode phòng mổ quan sát được",
        "features": FEATURE_COLUMNS,
        "trained_on": summary["dataset"]["source"], "dataset_sha256": summary["dataset"]["file_sha256"],
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_card": "data/DATA_CARD.md; docs/eda-report.md",
        "training_protocol": summary["protocol"], "random_seed": SEED,
        "library_versions": summary["environment"],
        "evaluation": {"held_out_staff_oof": held[SELECTED], "later_time_holdout": later[SELECTED],
                       "fold_mae": summary["stability"][SELECTED],
                       "reference_activity_median_oof": held[REFERENCE]},
        "selection_reason": "Tổng workload ít bị đánh giá thiếu hơn median (workload_sensitivity.json phần B); "
                            "RMSE/R² ngang GBT; hệ số đọc được theo hoạt động; inference là phép cộng.",
        "intended_use": "Thực nghiệm/so sánh phương pháp trên dữ liệu phòng mổ (OR). "
                        "Không dùng làm duration chăm sóc bệnh nhân nội trú.",
        "production": False,
        "limitations": [
            "Một phòng mổ Nhật Bản, 7 ngày tháng 7/2024, 37 nhân viên.",
            "Episode là khoảng hoạt động liên tục, không gắn bệnh nhân/ca mổ; thiếu acuity, ADL, kinh nghiệm.",
            "Thực chất chỉ một feature (task_name quyết định hai cột còn lại) → hệ số không phải feature importance độc lập.",
            "Vẫn đánh giá thiếu khoảng 35% episode; MAE cao hơn activity median.",
        ],
    }
    (ART / "or_ridge_v1.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    (ART / "or_ridge_v1.metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")


def sensitivity(oof):
    """A: tất định; B: ca synthetic ghép từ episode OR với dự đoán OOF thật."""
    rates = [0, 0.05, 0.10, 0.15, 0.20]
    part_a = [{"planned_min": w, "underestimate_pct": int(r * 100), "actual_min": round(w * (1 + r), 1),
               "free_time_min": round(SHIFT_MIN - w * (1 + r), 1)}
              for w in PLANNED_LEVELS.values() for r in rates]
    rng = np.random.default_rng(SEED)
    staff = oof[oof["split"] == "held_out_staff"].reset_index(drop=True)
    part_b = {}
    for model in COMPARE:
        pred, actual = staff[model].to_numpy(), staff[TARGET_COLUMN].to_numpy()
        per_level = {}
        for label, target in PLANNED_LEVELS.items():
            free, planned_sums = [], []
            for _ in range(5000):
                p_sum = a_sum = 0.0
                while p_sum < target:
                    i = rng.integers(len(pred))
                    p_sum += pred[i]
                    a_sum += actual[i]
                planned_sums.append(p_sum)
                free.append(SHIFT_MIN - a_sum)
            free = np.array(free)
            per_level[label] = {
                "simulations": 5000, "mean_planned_min": float(np.mean(planned_sums)),
                "free_time_median": float(np.median(free)), "free_time_p10": float(np.percentile(free, 10)),
                "p_free_lt_30": float((free < 30).mean()), "p_free_lt_60": float((free < 60).mean()),
                "p_overrun_shift": float((free < 0).mean()), "_free": free,
            }
        part_b[model] = per_level
    return part_a, part_b


def figures(summary, oof, part_a, part_b):
    FIG.mkdir(parents=True, exist_ok=True)
    staff = oof[oof["split"] == "held_out_staff"]
    y = staff[TARGET_COLUMN]

    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.hist(np.log10(y), bins=40, color="#4C72B0")
    ticks = [1, 5, 10, 30, 60, 120, 240, 420]
    ax.set_xticks(np.log10(ticks), ticks)
    ax.axvline(np.log10(y.median()), color="k", ls="--", lw=1, label="median %.0f phút" % y.median())
    ax.set(xlabel="Thời lượng episode (phút, thang log)", ylabel="Số episode",
           title="Phân phối thời lượng activity episode phòng mổ (n=%d)" % len(y))
    ax.legend(); fig.tight_layout(); fig.savefig(FIG / "l3_01_duration_distribution.png", dpi=130); plt.close(fig)

    held = summary["overall"]["held_out_staff"]
    stab = summary["stability"]
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    x = np.arange(len(MODELS))
    ax.bar(x - 0.2, [held[m]["mae"] for m in MODELS], 0.4,
           yerr=[stab[m]["fold_mae_std"] for m in MODELS], capsize=3, label="MAE (± SD giữa 5 fold)")
    ax.bar(x + 0.2, [held[m]["rmse"] for m in MODELS], 0.4, label="RMSE", color="#DD8452")
    ax.set_xticks(x, [LABELS[m] for m in MODELS], rotation=25, ha="right")
    ax.set(ylabel="Phút", title="So sánh mô hình — GroupKFold(5) theo staff, out-of-fold")
    ax.legend(); fig.tight_layout(); fig.savefig(FIG / "l3_02_model_comparison.png", dpi=130); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, m in zip(axes, (REFERENCE, SELECTED)):
        ax.scatter(staff[m], y, s=6, alpha=0.35)
        ax.plot([1, 450], [1, 450], "k--", lw=1)
        ax.set(xscale="log", yscale="log", xlabel="Dự đoán (phút)", title=LABELS[m])
    axes[0].set_ylabel("Thực tế (phút)")
    fig.suptitle("Thực tế vs dự đoán (out-of-fold); điểm trên đường chéo = đánh giá thiếu")
    fig.tight_layout(); fig.savefig(FIG / "l3_03_actual_vs_predicted.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.6))
    bins = np.linspace(-150, 150, 61)
    for m, c in ((REFERENCE, "#4C72B0"), (SELECTED, "#DD8452")):
        ax.hist(np.clip(staff[m] - y, -150, 150), bins=bins, alpha=0.55, label=LABELS[m], color=c)
    ax.axvline(0, color="k", lw=1)
    ax.set(xlabel="Dự đoán − thực tế (phút; âm = đánh giá thiếu; cắt ±150)", ylabel="Số episode",
           title="Phân phối residual")
    ax.legend(); fig.tight_layout(); fig.savefig(FIG / "l3_04_residuals.png", dpi=130); plt.close(fig)

    by_type = pd.read_csv(ART / "or_metrics_by_task_type.csv")
    pivot = by_type[by_type.model.isin([REFERENCE, SELECTED])].pivot(
        index="task_type", columns="model", values="mae")
    counts = by_type.groupby("task_type").n.first()
    pivot = pivot.loc[counts.sort_values().index]
    fig, ax = plt.subplots(figsize=(7.5, 5))
    yy = np.arange(len(pivot))
    ax.barh(yy - 0.2, pivot[REFERENCE], 0.4, label=LABELS[REFERENCE])
    ax.barh(yy + 0.2, pivot[SELECTED], 0.4, label=LABELS[SELECTED], color="#DD8452")
    ax.set_yticks(yy, ["%s (n=%d)" % (t, counts[t]) for t in pivot.index])
    ax.set(xlabel="MAE (phút)", title="Sai số theo task_type (out-of-fold)")
    ax.legend(); fig.tight_layout(); fig.savefig(FIG / "l3_05_error_by_task_type.png", dpi=130); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    a = pd.DataFrame(part_a)
    for w, g in a.groupby("planned_min"):
        axes[0].plot(g["underestimate_pct"], g["free_time_min"], marker="o", label="kế hoạch %d phút" % w)
    for level, ls in ((30, "--"), (60, ":")):
        axes[0].axhline(level, color="gray", ls=ls, lw=1)
        axes[0].text(20.2, level, " %d phút" % level, va="center", fontsize=8)
    axes[0].set(xlabel="Tổng workload bị đánh giá thiếu (%)", ylabel="Free time còn lại (phút)",
                title="A. Minh họa tất định — ca 480 phút")
    axes[0].legend(fontsize=8)
    label = "420 (Hybrid 60)"
    for m, c in ((REFERENCE, "#4C72B0"), (SELECTED, "#DD8452")):
        free = part_b[m][label]["_free"]
        axes[1].hist(np.clip(free, -300, 300), bins=60, alpha=0.5, color=c,
                     label="%s: P(free<30)=%.0f%%" % (LABELS[m], 100 * (free < 30).mean()))
    for level, ls in ((30, "--"), (60, ":")):
        axes[1].axvline(level, color="gray", ls=ls, lw=1)
    axes[1].set(xlabel="Free time thực tế (phút, cắt ±300)", ylabel="Số ca mô phỏng",
                title="B. SYNTHETIC từ episode OR — kế hoạch ≈420 phút")
    axes[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "l3_06_underestimate_free_time.png", dpi=130); plt.close(fig)


def main():
    summary = json.loads((ART / "or_experiment_summary.json").read_text(encoding="utf-8"))
    oof = pd.read_csv(ART / "or_oof_predictions.csv")
    export_selected(summary)
    part_a, part_b = sensitivity(oof)
    figures(summary, oof, part_a, part_b)
    clean_b = {m: {k: {kk: vv for kk, vv in v.items() if kk != "_free"} for k, v in lv.items()}
               for m, lv in part_b.items()}
    (ART / "workload_sensitivity.json").write_text(json.dumps({
        "label": "MINH HỌA — A tất định; B synthetic từ episode OR (không phải ca nội trú quan sát)",
        "shift_min": SHIFT_MIN, "seed": SEED, "source_predictions_sha256": sha256(ART / "or_oof_predictions.csv"),
        "assumptions": ["free time = 480 − workload thực tế; free time KHÔNG đồng nghĩa nghỉ thực tế",
                        "episode được lấy ngẫu nhiên có hoàn lại, độc lập, tới khi tổng DỰ ĐOÁN ≥ mức kế hoạch",
                        "không có việc phát sinh, không có overhead di chuyển"],
        "deterministic": part_a, "synthetic_or": clean_b,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for m, lv in clean_b.items():
        print("==", m)
        print(pd.DataFrame(lv).T.round(3).to_string())


if __name__ == "__main__":
    main()
