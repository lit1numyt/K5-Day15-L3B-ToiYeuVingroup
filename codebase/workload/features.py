"""Lấy feature ứng viên cho L3 từ instance; chỉ đọc, không suy ra giá trị.

Danh sách dưới đây là ỨNG VIÊN theo docs/feature-spec.md §2, chưa phải feature chốt.
Feature cuối cùng chỉ chốt sau khi nhóm dữ liệu xong EDA (feature-spec §5).
"""

# Feature biết được TRƯỚC khi xếp lịch. Không có feature điều dưỡng: lúc ước lượng
# chưa biết ai làm task (experience_years/skill_match chỉ có sau phân công).
TASK_FEATURES = ("task_type", "required_skill", "required_skill_level", "priority",
                 "frequency", "equipment_required", "prep_required")
PATIENT_FEATURES = ("acuity_score", "care_category", "adl_dependency",
                    "isolation_precaution", "tier", "workload_weight")
SHIFT_FEATURES = ("shift_length_min", "census")
CANDIDATE_FEATURES = TASK_FEATURES + PATIENT_FEATURES + SHIFT_FEATURES

# Không bao giờ được làm feature hay nhãn của L3:
# - mốc ghi log MIMIC (module-contract §3.3, B16/B17): là thời điểm ghi nhận, không phải thời gian thao tác;
# - target và kết quả phân công (feature-spec §2, rò rỉ).
FORBIDDEN_FEATURES = frozenset({
    "charttime", "storetime", "starttime", "endtime", "intime", "outtime",
    "timestamp_start", "timestamp_end", "actual_duration_min", "est_duration_min",
    "duration_source", "nurse_id", "assigned_nurse", "start", "end",
    "workload_minutes", "utilization", "end_of_shift_load",
})


def forbidden_in(names):
    """Trả các tên feature bị cấm có trong `names` (đã sắp xếp)."""
    return sorted(set(names) & FORBIDDEN_FEATURES)


def build_features(task, patient, shift):
    """Gộp feature ứng viên của một task. Trường không có thì không xuất hiện (không impute)."""
    features = {}
    for source, names in ((task, TASK_FEATURES), (patient or {}, PATIENT_FEATURES),
                          (shift or {}, SHIFT_FEATURES)):
        for name in names:
            if source.get(name) is not None:
                features[name] = source[name]
    return features
