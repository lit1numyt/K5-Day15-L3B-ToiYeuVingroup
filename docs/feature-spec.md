# NurseFlow — Feature spec / Từ điển dữ liệu (cho EDA & feature engineering)

> Đây là **cột cần có** cho mô hình, để nhóm dữ liệu (Lam, Kiên) làm EDA + feature engineering đúng
> hướng. Kiến trúc tổng: [`solution-design.md`](solution-design.md). Trường ★ = must-have, ◇ = full-richness.
> Ký hiệu vai trò: **key** (định danh/join) · **feat** (feature cho ML) · **target** (biến mục tiêu) ·
> **cons** (tham số ràng buộc cho solver L2).

## 0. "Mô hình" nào cần feature?

- **L2 · CP-SAT solver:** cần **cột đầu vào có cấu trúc** (key + tham số ràng buộc). Không "học", nhưng
  phải định nghĩa rõ kiểu/đơn vị.
- **L3 · Estimator (mô hình ML/DL):** đây là chỗ EDA + feature engineering thực sự phục vụ.
  **Target = thời lượng task (`actual_duration_min`)**, tuỳ chọn thêm `workload_points`.

→ Công sức feature engineering của nhóm dữ liệu **tập trung vào L3**. L2 chỉ cần schema sạch.

## 1. Schema thực thể (cột thô cần tìm/sinh)

### 1.1 Nurse — 1 dòng / điều dưỡng / ca

| Cột | Kiểu | Vai trò | ★/◇ | Ghi chú |
|---|---|---|---|---|
| `nurse_id` | str | key | ★ | |
| `shift_id` | str | key | ★ | |
| `skills` | set/multi-hot | feat, cons | ★ | vd `{IV, wound_care, ventilator, pediatric}` |
| `qualification_level` | ordinal | feat, cons | ★ | vd RN > LPN > aide |
| `experience_years` | num | feat | ★ | |
| `specialization` | cat | feat | ◇ | |
| `available_from`,`available_to` | time | cons | ★ | trong ca; **vắng = khoảng rỗng** |
| `max_capacity_min` | num | cons | ★ | phút làm việc tối đa trong ca |
| `home_zone` | cat | feat, cons | ◇ | cho gom việc theo vị trí |

### 1.2 Patient — 1 dòng / bệnh nhân trong khoa

| Cột | Kiểu | Vai trò | ★/◇ | Ghi chú |
|---|---|---|---|---|
| `patient_id` | str | key | ★ | |
| `ward_id` | str | key | ★ | |
| `acuity_score` | ordinal/num | feat | ★ | yếu tố chính đẩy thời lượng/workload |
| `care_category` | cat | feat | ★ | vd post-op, step-down, palliative |
| `adl_dependency` | ordinal | feat | ★ | mức phụ thuộc vận động/sinh hoạt — rất quyết định thời gian điều dưỡng |
| `isolation_precaution` | bool | feat | ◇ | tốn thời gian mặc đồ bảo hộ/chuẩn bị |
| `room`/`zone` | cat | feat, cons | ◇ | vị trí cho proximity clustering |

### 1.3 Task — 1 dòng / công việc trong ca (**đơn vị huấn luyện của L3**)

| Cột | Kiểu | Vai trò | ★/◇ | Ghi chú |
|---|---|---|---|---|
| `task_id` | str | key | ★ | |
| `patient_id` | str | key→join | ★ | |
| `task_type` | cat | feat, cons | ★ | med_admin, vitals, wound_care, hygiene, mobilization, admission, discharge, handover, documentation |
| `required_skill` | cat/set | cons | ★ | khớp với `nurse.skills` |
| `required_skill_level` | ordinal | cons | ★ | |
| `equipment_required` | multi-hot | feat, cons | ◇ | cho gom việc theo thiết bị |
| `prep_required` | bool | feat | ◇ | |
| `earliest_start` | time | cons | ★ | |
| `latest_finish`/`deadline` | time | cons | ★ | cửa thời gian |
| `priority` | ordinal | feat, cons | ★ | |
| `frequency` | cat | feat | ◇ | một lần vs định kỳ (q4h…) |
| `est_duration_min` | num | **target (dự đoán)** → cons | ★ | L3 xuất ra; nạp vào solver |
| `actual_duration_min` | num | **target (huấn luyện)** | ★ | chỉ có ở dữ liệu lịch sử |
| `compat_group_key` | derived | cons | ◇ | suy ra (zone+care_type+equipment) để clustering |
| `precedence_task_id` | str | cons | ◇ | thứ tự bắt buộc |

### 1.4 Ward / Shift — 1 dòng / ca

| Cột | Kiểu | Vai trò | ★/◇ | Ghi chú |
|---|---|---|---|---|
| `shift_id` | str | key | ★ | |
| `shift_length_min` | num | cons | ★ | |
| `coverage_rules` | bảng | cons | ★ | theo (zone × khung giờ): tối thiểu #điều dưỡng, tối thiểu kỹ năng (**cứng**) |
| `phase_structure` | bảng | cons | ◇ | cửa prep/care/recovery/next/handover |
| `break_policy` | bảng | cons | ◇ | số/độ dài giờ nghỉ, coverage khi nghỉ |
| `census`/`occupancy` | num | feat (context) | ★ | |

### 1.5 Activity log (lịch sử) — nguồn target cho L3

| Cột | Kiểu | Vai trò | Ghi chú |
|---|---|---|---|
| `task_id`,`nurse_id`,`patient_id` | str | key | |
| `timestamp_start`,`timestamp_end` | datetime | → target | hiệu = `actual_duration_min` |
| `actual_duration_min` | num | **target** | mục tiêu hồi quy |
| `workload_points` | num | target (phụ) | suy từ phương pháp McGill |
| `time_of_day`,`shift_phase` | cat | feat | |

## 2. Feature set của L3 estimator (sau engineering)

**Target:** `actual_duration_min` (hồi quy). Tuỳ chọn thứ hai: `workload_points`.

| Nhóm | Feature | Engineering |
|---|---|---|
| Patient | `acuity_score`, `care_category`, `adl_dependency`, `isolation_precaution` | ordinal giữ thứ tự; `care_category` OHE / target-encoding |
| Task | `task_type`, `required_skill_level`, `equipment_required`, `prep_required`, `priority`, `frequency` | `task_type`/`equipment` multi-hot; `priority` ordinal |
| Nurse | `experience_years`, `qualification_level`, `specialization`, `skill_match`(bool) | `skill_match` = nurse có `required_skill` không |
| Context | `time_of_day`, `shift_phase`, `census`, `is_handover_window` | `time_of_day` mã hoá **cyclical** (sin/cos); còn lại OHE |
| Spatial ◇ | `zone`, `distance_from_base` | cho overhead di chuyển |

**Nguyên tắc feature engineering:**
- Chuẩn hoá (standardize) biến số nếu dùng DL; cây (gradient boosting) không cần.
- Thiếu dữ liệu: impute `acuity` theo trung vị trong `care_category`, thêm cờ `*_was_missing`.
- Cardinality cao → target/frequency encoding thay OHE.

**⚠️ Rò rỉ (leakage) — TUYỆT ĐỐI tránh:** không dùng kết quả phân công (ai được giao, tải cuối ca,
thời điểm kết thúc) làm feature để dự đoán thời lượng — những cái đó chỉ biết **sau** khi đã lên lịch.
`actual_duration_min` là target, không bao giờ là feature.

**Fallback (nếu không có `actual_duration_min` lịch sử):** dùng `workload_points` (McGill) làm target
proxy, hoặc bảng tra `task_type × acuity → duration`. Khi đó **L3 là lookup/rule-based, không phải mô
hình học** — quyết định theo kết quả EDA.

## 3. Cột nào nạp ràng buộc nào của solver L2 (tham chiếu nhanh)

| Ràng buộc / mục tiêu | Cột dùng |
|---|---|
| Khớp kỹ năng (cứng) | `task.required_skill(_level)` ↔ `nurse.skills/qualification_level` |
| Coverage (cứng) | `ward.coverage_rules`, `nurse.available_*`, `patient.zone` |
| Cửa thời gian (cứng) | `task.earliest_start/deadline`, `est_duration_min` |
| Cân bằng tải (mềm) | tổng `est_duration_min` theo nurse → min CV / peak |
| Gom việc (mềm) ◇ | `compat_group_key` (zone+care_type+equipment) |
| Giờ nghỉ (mềm/cứng) ◇ | `break_policy`, `phase_structure`, coverage khi nghỉ |

## 4. Checklist EDA cho nhóm dữ liệu

- [ ] Phân phối & outlier của `actual_duration_min` theo `task_type`
- [ ] Mất cân bằng lớp của `task_type` (loại nào hiếm?)
- [ ] Tương quan `acuity`↔`duration`, `adl_dependency`↔`duration`
- [ ] % missing từng cột; cardinality các categorical
- [ ] Phân bố kỹ năng điều dưỡng (kỹ năng hiếm → rủi ro bất khả thi coverage)
- [ ] Mật độ task theo giờ (phát hiện khung giờ cao điểm → thiết kế phase)
- [ ] **Cổng quyết định:** dataset thực có timing cấp task không? (có → L3 học được; không → fallback)

## 5. Quyết định còn mở (chốt sau EDA)
- Target = `duration` / `workload_points` / cả hai?
- L3 = mô hình học hay lookup rule-based? (cổng: có `actual_duration_min` lịch sử không)
- Granularity huấn luyện: per-task (khuyến nghị) vs per-(patient, giờ)?
- Trường ◇ nào sống sót nếu dữ liệu thực mỏng?
