# NurseFlow — Cổng điều dưỡng

Chạy `python scripts/demo/serve_demo.py` từ gốc repo và mở http://localhost:8765.
Xem [hướng dẫn demo](../../scripts/demo/README.md) để cấu hình model thật.

Tài khoản tổng hợp của Khoa dùng chung mật khẩu demo `vinai_hackathon`.
`khoadhn` vào màn hình trưởng ca. Các tài khoản `annt`, `binhtv`, `cuclt`, `dungpm`,
`hoaht` vào màn hình điều dưỡng.

- **Trưởng ca** gửi yêu cầu trong chat để tạo bản nháp cho ca mẫu. Lịch và phần
  giải thích hiện sau khi hệ thống trả kết quả. Lịch mở ở khung giờ có phân công,
  có tùy chọn xem cả ca và bảng giờ bắt đầu/kết thúc của từng việc.
- **Điều dưỡng** thấy trạng thái chờ lịch đã duyệt. Bản thử dừng ở bước tạo bản
  nháp cho trưởng ca xem xét.

Giao diện dùng layout và tokens từ [design kit](../../style/STYLE.md). Các khối
trên lịch giữ tỷ lệ với thời lượng thực, theo phút kể từ đầu ca. Trên màn hình
hẹp, vùng lịch cuộn ngang và có bảng giờ để tra cứu.
