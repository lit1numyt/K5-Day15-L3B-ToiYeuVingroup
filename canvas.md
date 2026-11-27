# Canvas — Tôi Yêu Vingroup · Track B

> Điền ở guide bước 1.4. CP1 17:00 Thứ Sáu 27/11: nộp bản đầu, đủ 7 dòng (dòng 4 được ghi giả thuyết + nguồn sẽ kiểm).
> CP2 19:30 Thứ Sáu 27/11: cập nhật (số bằng chứng đầu, lát cắt đã chốt) và điền dòng "Đã đổi gì so với CP1".
> Track F: chép thêm thẻ đề của nhóm (khung trong file track F) xuống dưới bảng này.

| # | Dòng | Nhóm điền |
|---|---|---|
| 1 | Track + lát cắt dự kiến | Track B (Y tế) — **NurseFlow**: lập & điều phối phân công công việc điều dưỡng cho từng ca trực (theo kỹ năng, gom việc, chừa giờ nghỉ). |
| 2 | Người dùng chính (một vai cụ thể — không phải "học viên nói chung") | Điều dưỡng trưởng ca (nurse-in-charge) của một khoa nội trú cấp tính. |
| 3 | Pain một câu: ai — đang làm gì — vướng đâu — hậu quả | Điều dưỡng trưởng ca — đang lập phân công công việc đầu mỗi ca từ danh sách điều dưỡng trực và công việc — phải tự nhẩm cùng lúc ai đủ kỹ năng, tải đã bao nhiêu, task nào đến hạn, có đủ coverage không — nên phân công chậm, lệch tải, việc phân mảnh và mất giờ nghỉ thật của điều dưỡng. |
| 4 | Bằng chứng đầu | MatchRN v1.0.0: 703/1962 bản ghi (35,83%) tự báo overtime ≥30 phút ở ca gần nhất. Codebook mô tả C2.6: “Overtime on the last shift”. Script/cách đếm: `evidence/data-mining.md`. Đây là khảo sát điều dưỡng Thụy Sĩ, chưa chứng minh nguyên nhân phân công hay pain trưởng ca tại khoa Việt Nam. |
| 5 | **Lát cắt MỘT CÂU** (1 người dùng · 1 việc · 1 quyết định AI · 1 kết quả) | Đầu mỗi ca, điều dưỡng trưởng ca nhập danh sách điều dưỡng trực (kỹ năng, khả năng sẵn sàng — người vắng để trống) và danh sách công việc của ca → AI đề xuất kế hoạch phân công cả ca (gán việc theo kỹ năng, gom việc tương thích, chừa giờ nghỉ, không vi phạm coverage) → trả **bản nháp kế hoạch ca** để trưởng ca duyệt. |
| 6 | AI tự làm đến đâu + 1 dòng lý do: sai thì ai chịu gì | **AI gợi ý, người quyết** — chỉ tạo bản nháp, trưởng ca duyệt mới áp dụng. Lý do: phân công sai ảnh hưởng an toàn người bệnh; sai thì người bệnh/điều dưỡng chịu, nên người phải là chốt chặn cuối. |
| 7 | Phân công có tên | Khoa: luồng agent + spec/canvas · Lam: phân tích dữ liệu, lập lịch và kiểm kịch bản CP2 · Kiên: nghiên cứu tiêu chí dữ liệu và đề xuất nguồn MIMIC-IV Demo · Tiệp: dashboard + mô phỏng chi phí. |
| — | *(CP2)* Đã đổi gì so với CP1 | Bổ sung EDA MatchRN, contract và validator; 15 fixture kiểm engine và 6 câu có nguồn cho benchmark nhóm; L3 dùng duration đầu vào, thiếu thì hỏi. Giữ lát cắt đầu ca, chưa train duration model. |
