"""Công cụ đánh giá estimator L3 (chỉ thư viện chuẩn). Chưa có kết quả: chưa có dataset.

Ưu tiên an toàn: dự đoán THẤP hơn thực tế khiến L2 tính thiếu workload và dư free time,
nên ngoài MAE/RMSE/R² luôn báo riêng tỷ lệ và mức đánh giá thiếu.
"""
import math
import statistics

from .features import forbidden_in


def regression_metrics(y_true, y_pred):
    if len(y_true) != len(y_pred) or not y_true:
        raise ValueError("y_true và y_pred cần cùng độ dài, không rỗng")
    errors = [p - t for t, p in zip(y_true, y_pred)]
    mean_true = statistics.fmean(y_true)
    ss_tot = sum((t - mean_true) ** 2 for t in y_true)
    under = [-e for e in errors if e < 0]
    return {
        "n": len(errors),
        "mae": statistics.fmean(abs(e) for e in errors),
        "rmse": math.sqrt(statistics.fmean(e * e for e in errors)),
        "r2": 1 - sum(e * e for e in errors) / ss_tot if ss_tot else None,
        "underestimate_rate": len(under) / len(errors),
        "mean_underestimate_min": statistics.fmean(under) if under else 0.0,
        "max_underestimate_min": max(under, default=0),
    }


def metrics_by_group(y_true, y_pred, groups):
    """Sai số theo nhóm (task_type, acuity…)."""
    buckets = {}
    for t, p, g in zip(y_true, y_pred, groups):
        buckets.setdefault(g, ([], []))
        buckets[g][0].append(t)
        buckets[g][1].append(p)
    return {g: regression_metrics(t, p) for g, (t, p) in sorted(buckets.items(), key=lambda x: str(x[0]))}


def compare_to_baseline(model, baseline):
    """So hai dict từ regression_metrics; số âm = model tốt hơn baseline."""
    return {k: model[k] - baseline[k] for k in ("mae", "rmse", "underestimate_rate")}


def group_split(rows, key, test_ratio=0.2):
    """Chia train/test theo nhóm (vd patient_id, shift_id) để cùng bệnh nhân không nằm ở cả hai.

    Tất định: sắp nhóm theo tên, lấy phần cuối làm test. Không xáo ngẫu nhiên.
    """
    names = sorted({row[key] for row in rows}, key=str)
    if len(names) < 2:
        raise ValueError("cần ít nhất 2 nhóm để chia")
    cut = max(1, round(len(names) * test_ratio))
    test_names = set(names[-cut:])
    return ([r for r in rows if r[key] not in test_names],
            [r for r in rows if r[key] in test_names])


def leakage_issues(feature_names, train_rows=None, test_rows=None, group_key=None):
    """Kiểm rò rỉ: feature bị cấm, và nhóm trùng giữa train/test."""
    issues = ["feature bị cấm: " + f for f in forbidden_in(feature_names)]
    if group_key and train_rows is not None and test_rows is not None:
        shared = {r[group_key] for r in train_rows} & {r[group_key] for r in test_rows}
        if shared:
            issues.append("%d giá trị %s xuất hiện ở cả train và test" % (len(shared), group_key))
    return issues
