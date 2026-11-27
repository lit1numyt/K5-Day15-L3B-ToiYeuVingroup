# Data card — dữ liệu bản chạy thử dùng

> Điền ở guide bước 2.4 (bản đầu ở CP2, đủ ở CP3). Ôn lại: ngày 6 · lab ngày 6. Chấm ở rubric R4.
> Một trang. Mỗi dataset một mục. Dữ liệu chạy thử (bài mẫu, thông báo mẫu, đoạn transcript…) để trong thư mục `data/` này.
> Không commit nguyên tài liệu khoá, dữ liệu cá nhân thật hay nguyên file data BTC cấp — chỉ đoạn trích ngắn, bản viết lại, hoặc số đã tổng hợp.

> **Stub cho nhóm EDA (Lam, Kiên):** mỗi nguồn dưới đây là một mục cần điền trong lúc tìm/kiểm dữ liệu.
> Xem trường cần lấy ở [`docs/solution-design.md`](../docs/solution-design.md) §5. Điền `__`, sửa nếu nguồn không dùng được.

## Dataset 1 · Nurse Rostering Benchmarks (schedulingbenchmarks.org) + KU Leuven

| | |
|---|---|
| Dùng để làm gì | luật coverage, ràng buộc staffing, cấu trúc ca/instance cho engine L2 |
| Từ đâu | công khai: schedulingbenchmarks.org/nrp · gent.cs.kuleuven.be/nurserostering.html |
| Xử lý những bước gì | lọc __ · làm sạch __ · ánh xạ sang schema NurseFlow __ (script: `…`) |
| Số dòng / số đoạn | __ |
| Phiên bản / ngày lấy | __ |
| Nhãn | thật |
| Giới hạn | **không có task cấp điều dưỡng kèm thời lượng/deadline** — cần synthetic lấp |

## Dataset 2 · McGill Nursing Workload Tool

| | |
|---|---|
| Dùng để làm gì | phương pháp tính workload/acuity → nạp L3 estimator (hoặc rule-based) |
| Từ đâu | công khai: borealisdata.ca (doi:10.5683/SP4/L1ZBLT) |
| Xử lý những bước gì | trích thang điểm workload __ · ánh xạ acuity→thời lượng __ |
| Số dòng / số đoạn | __ |
| Phiên bản / ngày lấy | __ |
| Nhãn | thật |
| Giới hạn | là phương pháp tính, không phải lịch cá nhân từng điều dưỡng |

## Dataset 3 · MatchRN (University of Basel)

| | |
|---|---|
| Dùng để làm gì | mẫu ca trực thực, staffing, perceived workload → kiểm tính thực tế + feature cho L3 |
| Từ đâu | công khai: zenodo.org/records/15248072 |
| Xử lý những bước gì | lọc __ · ẩn danh __ · tổng hợp __ |
| Số dòng / số đoạn | __ |
| Phiên bản / ngày lấy | __ |
| Nhãn | thật |
| Giới hạn | __ (cần kiểm có task cấp giờ không) |

## Dataset 4 · Kịch bản khoa `synthetic` (nhóm tự sinh)

| | |
|---|---|
| Dùng để làm gì | instance đầy đủ (nurse·patient·task·ward) cho engine + bộ câu thử |
| Từ đâu | sinh có seed, tham số hoá theo phân phối thực từ Dataset 1–3 |
| Xử lý những bước gì | sinh __ · kiểm tay __ dòng (người kiểm: __) |
| Số dòng / số đoạn | __ |
| Phiên bản / ngày lấy | __ |
| Nhãn | `synthetic` |
| Giới hạn | **không phải bằng chứng pain**; phải khớp phân phối thực để đáng tin |

**Data `synthetic` (nhóm tự sinh):** ghi cách sinh (prompt / script), seed, người kiểm, số dòng đã kiểm tay. Data tự dựng **không phải bằng chứng pain**.

*(Tuỳ chọn · CMS Payroll-Based Journal: số liệu staffing bối cảnh — thêm mục nếu dùng.)*
