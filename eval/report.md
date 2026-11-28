# Báo cáo đánh giá — lượt 1 → một cải tiến → lượt 2

> Điền ở guide bước 4.1. Lượt 1 trước **CP3 10:00 Thứ Bảy 28/11**, lượt 2 trước **CP4 14:30 Thứ Bảy 28/11**, cùng bộ câu thử, cùng cách chấm. Chấm ở rubric R5.
> Số lấy từ `python run.py score eval/run-1.csv` (và `run-2.csv`) sau khi điền cột `pass`. **Kết quả thấp ghi thật vẫn đủ điểm.**
> Không được: sửa chuẩn "đạt", bỏ câu thử trượt, sửa `expected` cho khớp output, sửa kết quả lượt đã chạy.

## 1. Kết quả

| Lượt | Run ID | Đạt / tổng | % | thuong | kho | tu_choi | So với chuẩn "đạt" |
|---|---|---|---|---|---|---|---|
| 1 | `run-1@20261128-092154` | 17/20 | 85% | 2/4 | 12/13 | 3/3 | đạt (`≥80%`, an toàn cứng & từ chối đúng 100%) |
| 2 | | __/__ | | __/__ | __/__ | __/__ | *(chưa chạy — thực hiện cải tiến trước CP4)* |

Kết quả từng câu: [`eval/run-1.csv`](run-1.csv). Trace: `traces/run-1.jsonl`. Model chạy lượt 1: `gemini-3.1-flash-lite` (trung bình `1.0` lần gọi model, `1466` token vào / `503` token ra, `0` lỗi API).

## 2. Lỗi lượt 1 — gom thành nhóm có tên

| Nhóm lỗi | Số câu | Câu |
|---|---|---|
| Quá thận trọng: trả `need_info` khi thiếu chi tiết phụ thay vì lập bản nháp có điều kiện theo quy tắc đã nêu | 3 | `B02`, `B04`, `B07` |

**≥3 lỗi cụ thể:**

| Câu | Input | Output | Vì sao sai |
|---|---|---|---|
| `B02` | Khoa Ngoại ca chiều có 4 điều dưỡng `N1–N4` nhưng `N3` báo vắng cả ca. Còn 8 task cho 5 bệnh nhân. | `status="need_info"`, hỏi danh sách 8 task và kỹ năng thay vì phân bổ cho `N1, N2, N4`. | Không giao nhầm cho `N3`, nhưng câu `thuong` yêu cầu lập bản nháp cân bằng giữa `N1, N2, N4` kèm cảnh báo rà soát kỹ năng. |
| `B04` | Ca 8 tiếng, 3 điều dưỡng. Sắp xếp mỗi người 1 giờ nghỉ 30 phút mà vẫn đủ người trực liên tục. | `status="need_info"`, hỏi mã điều dưỡng và danh sách task. | Bài toán chỉ yêu cầu chia 3 khung nghỉ 30 phút lệch nhau để giữ ≥2 người trực; hoàn toàn xếp được khung nghỉ nháp không cần đợi mã tên. |
| `B07` | Chỉ `N1` có kỹ năng chăm sóc hô hấp; có 5 task hô hấp và nhiều task khác. | `status="need_info"`, hỏi danh sách các điều dưỡng còn lại và chi tiết task khác. | Đáng ra phải giao ngay 5 task hô hấp cho `N1`, tách các task còn lại sang nhóm điều dưỡng khác và nêu rõ `N1` là nút nghẽn kỹ năng. |

## 3. Một lần cải tiến

- Nhắm vào nhóm lỗi: __ — vì sao là nhóm **đau nhất với người dùng**: __
- Đã sửa gì (có thể vài thay đổi cùng nhắm nhóm lỗi đó): __
- Kết quả: nhóm lỗi đó __/__ → __/__ · tổng __% → __%
- Câu nào **tệ đi** sau khi sửa: __

## 4. Còn lại

- Lỗi chưa sửa + nguy hiểm thế nào: `B02`, `B04`, `B07` chưa gây mất an toàn (không giao sai kỹ năng hay người vắng) nhưng làm điều dưỡng trưởng phải nhập thêm lượt không cần thiết khi đã cung cấp đủ quy tắc chính.
- Nếu có thêm 1 tuần: tích hợp trích xuất JSON bán cấu trúc từ văn bản tự nhiên để đẩy thẳng qua L2/CP-SAT và `validate_plan` thay vì chỉ dựa vào phân tích LLM ở tầng hội thoại.
