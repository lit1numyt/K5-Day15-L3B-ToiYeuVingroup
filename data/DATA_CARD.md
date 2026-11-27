# Data card — dữ liệu bản chạy thử dùng

> Điền ở guide bước 2.4 (bản đầu ở CP2, đủ ở CP3). Ôn lại: ngày 6 · lab ngày 6. Chấm ở rubric R4.
> Một trang. Mỗi dataset một mục. Dữ liệu chạy thử (bài mẫu, thông báo mẫu, đoạn transcript…) để trong thư mục `data/` này.
> Không commit nguyên tài liệu khoá, dữ liệu cá nhân thật hay nguyên file data BTC cấp — chỉ đoạn trích ngắn, bản viết lại, hoặc số đã tổng hợp.

Chi tiết phân tích EDA đa nguồn, biểu đồ và kết quả cổng quyết định L3: xem [`docs/eda-report.md`](../docs/eda-report.md) và [`docs/feature-spec.md`](../docs/feature-spec.md).

## Dataset 1 · KU Leuven Nurse Rostering Benchmarks (`psmet1/nrp`)

| | |
|---|---|
| Dùng để làm gì | luật coverage theo kỹ năng/trình độ kinh nghiệm, cơ cấu ca trực, giờ nghỉ giữa ca, kịch bản `Normal` / `Overload` / `Absence` cho solver L2 |
| Từ đâu | công khai: `github.com/psmet1/nrp` (`data set 2` + `data set 1/Input` của 4 khoa lâm sàng: `Emergency`, `Geriatrics`, `Psychiatry`, `PalliativeCare`) |
| Xử lý những bước gì | lọc 4 khoa lâm sàng (bỏ `Meal Preparation`, `Reception`, `SampleOutput/`) · parse XML `data_set_2` kết hợp `StartTimeBreak`/`EndTimeBreak` từ `data_set_1` → xuất `nrp_wards_summary.csv`, `nrp_nurses.csv`, `nrp_shifts.csv`, `nrp_coverage_rules.csv` (script: [`scripts/data/extract_nrp.py`](../scripts/data/extract_nrp.py)) |
| Số dòng / số đoạn | 27 tệp XML/XSD/README → 12 instance khoa-kịch bản, 282 bản ghi điều dưỡng-kịch bản, 73 định nghĩa ca, 4.422 luật coverage |
| Phiên bản / ngày lấy | master · 2026-11-28 |
| Nhãn | thật |
| Giới hạn | **không có task cấp bệnh nhân kèm thời lượng/acuity** — cần ghép với Dataset 2 & 3 |

## Dataset 2 · Zenodo `20754938` — OR Nursing Time-and-Motion Records (Nhật Bản)

| | |
|---|---|
| Dùng để làm gì | thời lượng thực tế cấp tác vụ (`actual_duration_min`), phân bố theo giờ trong ngày, tỷ trọng trực tiếp/gián tiếp/nghỉ cho huấn luyện L3 |
| Từ đâu | công khai: `zenodo.org/records/20754938` (`doi:10.5281/zenodo.20754938`, `Data.xlsx`) |
| Xử lý những bước gì | kiểm tra MD5 (`78e04eb6c4ffcf2b599afd3080f97c21`) · dịch 100% nhãn cột và 46 tên tác vụ, 13 nhóm, 17 mã ca từ tiếng Nhật → tiếng Anh · quy đổi giờ/ngày Excel → ISO & phút · gộp các block quan sát 10 phút liên tiếp thành tập tác vụ liên tục → `zenodo_tasks_en.csv` & `zenodo_task_episodes_en.csv` (script: [`scripts/data/translate_zenodo.py`](../scripts/data/translate_zenodo.py)) |
| Số dòng / số đoạn | 11.074 dòng block quan sát → 2.390 tập tác vụ liên tục (`1.545,3` giờ, 37 nhân sự) |
| Phiên bản / ngày lấy | v1 (tháng 7/2024) · kiểm tra 2026-11-28 |
| Nhãn | thật (đã ẩn danh `職員No`) |
| Giới hạn | bối cảnh phòng mổ (OR), chưa có biến `patient_acuity` / `adl_dependency` đi kèm từng tác vụ |

## Dataset 3 · eICU Collaborative Research Database Demo v2.0.1

| | |
|---|---|
| Dùng để làm gì | hồ sơ bệnh nhân hồi sức cấp tính (`acuity_score` từ APACHE IV/IVa + `carePlanGeneral`, `adl_dependency` từ `Hygiene/ADLs` + `Activity`, cách ly, thở máy) và nhu cầu tác vụ điều dưỡng theo ca 8 giờ |
| Từ đâu | công khai: PhysioNet eICU Demo v2.0.1 (tổng hợp tại `data/eicu-collaborative-research-database-demo-2.0.1/`, loại khỏi git qua `.gitignore` vì nặng 137 MB) |
| Xử lý những bước gì | nối 12 bảng lâm sàng/điều dưỡng (`patient`, `hospital`, `apachePatientResult`, `apacheApsVar`, `carePlanGeneral`, `nurseCare`, `nurseAssessment`, `nurseCharting`, `medication`, `infusiondrug`, `treatment`, `intakeOutput`) · tính `acuity_score` (1–5), `adl_dependency` (1–4) và tổng hợp cụm tác vụ trong 24h đầu → `eicu_patients.csv` & `eicu_shift_tasks.csv` (script: [`scripts/data/extract_eicu.py`](../scripts/data/extract_eicu.py)) |
| Số dòng / số đoạn | 2.520 lượt bệnh nhân ICU (`292` khoa, `186` bệnh viện) · 28.697 cụm tác vụ theo ca 8 giờ |
| Phiên bản / ngày lấy | v2.0.1 · 2026-11-28 |
| Nhãn | thật (đã khử định danh theo chuẩn PhysioNet) |
| Giới hạn | ghi nhận thời điểm thực hiện tác vụ (`offset`), không ghi thời lượng kéo dài từng tác vụ |

## Dataset 4 · Bảng ghép nối 3 nguồn & Feature Engineering (`processed`)

| | |
|---|---|
| Dùng để làm gì | bảng huấn luyện L3 không rò rỉ dữ liệu (`l3_task_features_zenodo_real.csv`), bảng đầy đủ schema [`feature-spec.md`](../docs/feature-spec.md) (`harmonized_nurseflow_tasks.csv`), và bảng kịch bản khoa-ca cho solver L2 / baseline L4 (`harmonized_ward_shift_instances.csv`) |
| Từ đâu | ghép nối Dataset 1–3 qua [`scripts/data/harmonize_and_engineer.py`](../scripts/data/harmonize_and_engineer.py) · EDA qua [`scripts/eda/run_eda.py`](../scripts/eda/run_eda.py) |
| Xử lý những bước gì | ánh xạ phân loại tác vụ & khung giờ · mã hoá cyclical `time_of_day_sin/cos` · gắn `shift_phase`, `compat_group_key`, `required_skill_level`, hiệu chỉnh `calibrated_shift_task_min` (có gắn nhãn rõ là proxy hiệu chỉnh, không phải đo bấm giờ trực tiếp trên eICU) |
| Số dòng / số đoạn | `l3_task_features_zenodo_real.csv`: 2.390 × 36 cột · `harmonized_nurseflow_tasks.csv`: 28.697 × 42 cột · `harmonized_ward_shift_instances.csv`: 12 × 25 cột (đều 0% missing) |
| Phiên bản / ngày lấy | 2026-11-28 |
| Nhãn | kết hợp `thật` (Dataset 1–3) + `proxy hiệu chỉnh` (thời lượng điều chỉnh theo acuity/ADL) |
| Giới hạn | trường `calibrated_shift_task_min` và `workload_points` trên bảng ghép là ước lượng quy đổi chéo nguồn (chỉ dùng cho mô phỏng/L2, không thay thế bằng chứng bấm giờ lâm sàng trực tiếp) |
