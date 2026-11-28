# Reflection — Đồng Hữu Nguyên Khoa

> Nguyễn Đức Khương Lam tổng hợp và nộp theo ủy quyền của Khoa vì Khoa có việc riêng. Nội dung được đối chiếu với commit, tài liệu và kết quả đã lưu của nhóm.

1. **Vai trò và phần việc**

   Khoa là đội trưởng. Ở CP1–CP2, Khoa chốt Track B, định hình lát cắt lập phân công đầu ca và phụ trách thiết kế hệ thống. [CP1](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/commit/80e33b3) · [Thiết kế](../docs/solution-design.md)\
   Ở CP3, Khoa chốt schema và hợp đồng giữa L1–L4, triển khai taxonomy bệnh nhân bằng KMeans có phương án dự phòng theo quy tắc và hai baseline theo số bệnh nhân hoặc trọng số acuity. [Contract](../docs/module-contract.md) · [PR #4](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/4) · [PR #8](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/8)\
   Khoa viết các ca kiểm taxonomy và baseline, phát triển giao diện demo, nối model thật và chạy lượt đánh giá GPT‑4o mini. Lượt 2 lưu 14/20 theo nhãn chấm trong repo. [Test L4](../tests/test_l4_baseline.py) · [PR #16](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/16) · [Báo cáo đánh giá](../eval/report.md)\
   Ở CP4 và sau demo, Khoa chuẩn bị slide pitch, tích hợp bản web và sửa phần lịch điều dưỡng. Lam phụ trách L2 và validator, Kiên phụ trách L1, Tiệp phụ trách L3. [PR #21](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/21) · [Sửa lịch điều dưỡng](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/commit/82fae78)

2. **AI hỗ trợ thế nào**

   Khoa phụ trách kiến trúc, hợp đồng module và lựa chọn phương pháp L4. Codex hỗ trợ nhóm rà tích hợp, sửa lỗi và kiểm luồng chạy theo thiết kế đó. [Khai báo dùng AI](../docs/ai-usage.md)\
   Lượt đánh giá của Khoa sử dụng GPT‑4o mini làm model được thử. Kết quả được lưu theo từng câu trong CSV và trace để nhóm đối chiếu. [CSV lượt 2](../eval/run-2.csv) · [Trace lượt 2](../traces/run-2.jsonl)\
   Commit sửa giao diện có ghi nhận Claude Opus 4.8 hỗ trợ. Khi lịch điều dưỡng dồn trái dù giờ trong dữ liệu đúng, Khoa sửa bố cục vùng lịch để thanh công việc hiện đúng theo trục giờ. [Commit sửa lỗi](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/commit/82fae78)

3. **Một câu thử trượt của nhóm và bài học**

   B08 ở lượt 2 có hai việc ưu tiên cao cùng hạn trước 09:00 và chỉ một điều dưỡng đủ kỹ năng đang rảnh. Model hỏi thêm về bệnh nhân, nội dung và thời lượng, nhưng chưa nêu cách xử lý xung đột thời hạn. Câu được chấm `pass=0`. [Kết quả lượt 2](../eval/run-2.csv)\
   Hỏi thời lượng là cần thiết để đánh giá khả thi. Câu trả lời vẫn có thể chỉ ra nút nghẽn và đề xuất trưởng ca xác nhận thứ tự ưu tiên, tìm người hỗ trợ đủ kỹ năng hoặc xem xét giãn hạn. [Bộ câu thử](../eval/benchmark.csv)\
   Bài học từ lần đối chiếu là cần tách hai việc: nêu phương án có điều kiện ngay khi nhận ra xung đột, và kiểm thời lượng cùng các ràng buộc trước khi kết luận lịch khả thi. [Phân tích lỗi](../eval/report.md)
