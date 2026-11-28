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
| `available_from`,`available_to` | time | cons | ★ | trong ca; **vắng = loại khỏi nurses[] theo module contract** |
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
| `timestamp_start`,`timestamp_end` | datetime | → target | hiệu là duration khi hai mốc quan sát thao tác của đúng nurse/task |
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
- Với dữ liệu quan sát liên kết, có thể fit imputer acuity theo care_category trên train và thêm cờ thiếu. Preliminary hiện thiếu liên kết này nên giữ unknown.
- Cardinality cao → target/frequency encoding thay OHE.

**⚠️ Rò rỉ (leakage) — TUYỆT ĐỐI tránh:** không dùng kết quả phân công (ai được giao, tải cuối ca,
thời điểm kết thúc) làm feature để dự đoán thời lượng — những cái đó chỉ biết **sau** khi đã lên lịch.
`actual_duration_min` là target, không bao giờ là feature.

**Fallback sau EDA:** thời lượng đã cho hoặc lookup task phù hợp từ Simmons Table 3,
đơn vị phút, nguồn ghi trong task. McGill hỗ trợ taxonomy/workload; dữ liệu đã kiểm chưa
cung cấp phép đổi điểm thành phút. Điều kiện sử dụng ở [module contract §3.3](module-contract.md).

## 3. Cột nào nạp ràng buộc nào của solver L2 (tham chiếu nhanh)

| Ràng buộc / mục tiêu | Cột dùng |
|---|---|
| Khớp kỹ năng (cứng) | `task.required_skill(_level)` ↔ `nurse.skills/qualification_level` |
| Coverage (cứng) | `ward.coverage_rules`, `nurse.available_*`, `patient.zone` |
| Cửa thời gian (cứng) | `task.earliest_start/deadline`, `est_duration_min` |
| Cân bằng tải (mềm) | tổng `est_duration_min` theo nurse → min CV / peak |
| Gom việc (mềm) ◇ | `compat_group_key` (zone+care_type+equipment) |
| Giờ nghỉ (mềm/cứng) ◇ | `break_policy`, `phase_structure`, coverage khi nghỉ |

## 4. Kết quả checklist EDA

| Nội dung | Kết quả và bằng chứng |
|---|---|
| Phân phối/outlier và mất cân bằng nhóm | Bảng theo nhóm task, p95 và outlier trong báo cáo §4.1 và duration_by_type.csv. |
| Acuity/ADL ↔ duration | Chưa ước tính được vì thiếu quan sát patient-task liên kết. |
| Missing/cardinality | Báo cáo §3–4 và missingness.csv, mẫu số theo từng bước. |
| Kỹ năng hiếm | Roster NRP có 1/27 người mang skill 175 ở Emergency. Coverage theo ca cần availability/level. |
| Mật độ theo giờ | Phần giao segment–giờ và số lượt bắt đầu episode, báo cáo §4.1. |
| Cổng lựa chọn L3 | Zenodo có timing activity OR; nội trú dùng given/lookup có điều kiện theo nguồn Simmons. |

## 5. Lựa chọn sau Preliminary

- Target thực nghiệm là actual_duration_min của episode OR. Feature table có 2.192 dòng,
  chọn task_name cho tra median; giữ hai nhóm để đối chứng. Staff ID dùng chia tập.
- Lookup nội trú theo task là phương án CP3 hiện có căn cứ. Việc học acuity/ADL/experience
  cần nguồn quan sát liên kết phù hợp với đơn vị task của bệnh nhân.
- Bộ ca chung cung cấp nurse, patient, task, shift theo module contract với giả định kỹ thuật
  được ghi riêng. Khoa có thể phát triển taxonomy/baseline, Tiệp kiểm L3, Lam kiểm L2,
  Kiên kiểm workflow trên cùng input. [Bộ bàn giao](../data/preliminary/README.md).
- Các trường ★/◇ ở §1 là schema đích. Trường cần cho solver lấy từ input được xác nhận hoặc
  kịch bản có khai báo; tính sẵn có của dữ liệu train được ghi trong báo cáo Preliminary.
