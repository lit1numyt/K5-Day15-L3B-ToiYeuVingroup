# Demo luồng NurseFlow

Một demo chạy được, nối các mảnh đã có thành một luồng lập kế hoạch ca:

```
python -m pip install -r requirements.txt
python scripts/demo/run_demo.py
```

L2 dùng OR-Tools CP-SAT. Provider lấy từ môi trường hoặc `.env` theo `.env.example`.
Để kiểm luồng cục bộ, đặt `MODEL_PROVIDER=fake`. Để đo AI thật, cấu hình provider,
model và API key rồi chạy lại. L4 dùng KMeans khi nạp được model, có rule fallback.

Luồng demo trên một ca mẫu (`data/preliminary/instances.json`, case P02):
1. **[L3] `estimate_duration`** — điền thời lượng việc còn thiếu từ bảng Simmons (gắn nhãn
   `lookup:simmons…`), giữ nguyên thời lượng đã cho (`given`).
2. **[L4] `classify_patient`** — xếp bệnh nhân thành tier nhẹ/trung bình/nặng.
3. **[Engine] `answer()`** — L2 CP-SAT lập bản nháp và `validate_plan` kiểm lại
   kỹ năng, deadline, capacity, di chuyển, nghỉ và coverage.
4. **[L4] `baseline_allocate`** — so với cách truyền thống (theo đầu bệnh nhân và acuity-weighted)
   trên cùng ca. Script in các chỉ số đo được của từng phương pháp.

Kết thúc ở trạng thái `draft` (`approval_required=true`) — AI đề xuất, trưởng ca duyệt.

## Demo web tương tác

1. Cài `requirements.txt` và cấu hình provider thật trong `.env` theo [mẫu](../../.env.example).
2. Chạy `python scripts/demo/serve_demo.py` từ gốc repo. Lệnh chỉ mở web server local.
3. Mở http://localhost:8765 và đăng nhập trưởng ca bằng `khoadhn` /
   `vinai_hackathon` (tài khoản demo).
4. Nhập **Lập bản nháp phân công cho ca mẫu 07:00–15:00.** và bấm **Gửi** hoặc Enter.
5. Xem phản hồi, lịch cả ca và bảng giờ chi tiết. Trạng thái cuối là
   **Bản nháp chờ trưởng ca duyệt**.

Ca tổng hợp của Khoa có 5 điều dưỡng, 20 bệnh nhân và 48 công việc. Model phân loại
yêu cầu, sau đó agent dùng luồng JSON hiện có để lập lịch và giải thích. Chỉ yêu cầu
lập bản nháp cho ca mẫu với các ràng buộc sẵn có mới đi vào solver. Giờ làm việc,
nhân sự và ràng buộc lấy từ ca mẫu. Trang hiển thị số token đo được trong lần xử lý.

Tài khoản điều dưỡng không thể gọi API lập lịch. Bản nháp chỉ hiện ở phiên trang
trưởng ca vừa gửi yêu cầu, không xuất thành lịch đã duyệt hoặc ghi đè file kết quả.
Cổng chạy trên loopback với tài khoản mẫu công khai, phục vụ demo dữ liệu tổng hợp.

`python scripts/demo/build_demo.py` vẫn có thể xuất snapshot riêng để kiểm pipeline.
Cổng tương tác không nạp snapshot này.

Khoa phát triển demo/UI. Các module giữ phân công theo
[contract](../../docs/module-contract.md). Codex hỗ trợ triển khai và kiểm tích hợp.
