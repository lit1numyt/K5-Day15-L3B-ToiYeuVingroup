# Reflection — Nguyễn Đức Khương Lam

1. **Vai trò và phần việc**

   Từ CP1, tôi tham gia nghiên cứu bối cảnh và nhu cầu phân công điều dưỡng đầu ca. Ở CP2, tôi phân tích MatchRN, đối chiếu MIMIC Demo theo nghiên cứu của Kiên và bổ sung ca kiểm cho phần lập lịch. [Bằng chứng dữ liệu](../evidence/data-mining.md) · [PR CP2](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/2)\
   Ở CP3, tôi cùng Kiên thực hiện Preliminary và chọn cách sử dụng nhãn thời lượng theo ngữ cảnh của từng nguồn. Zenodo phục vụ EDA hoạt động phòng mổ, còn L3 nội trú dùng thời lượng đã cung cấp hoặc tra bảng tham chiếu khi đủ điều kiện. [Báo cáo Preliminary](../docs/eda-report.md)\
   Tôi phụ trách thiết kế và triển khai L2 CP-SAT, validator và kiểm đối chứng theo kiến trúc của Khoa. Kiên phụ trách L1, Tiệp phụ trách L3, Khoa phụ trách kiến trúc, contract và L4. [Báo cáo L2](../eval/cp3-engine-report.md) · [PR #12](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/12)\
   Tôi trực tiếp thực hiện video demo CP3. Ở CP4, tôi hỗ trợ tích hợp chat để trưởng ca gửi yêu cầu trước khi hệ thống lập bản nháp, đồng thời kiểm cách hiển thị lịch trên ca tổng hợp. [PR #20](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/20)

2. **AI hỗ trợ tôi thế nào**

   Tôi chịu trách nhiệm về các quyết định trong phần mình phụ trách, từ tiêu chí chọn dữ liệu đến cách mô hình hóa và kiểm ràng buộc của L2. Codex hỗ trợ tìm và đối chiếu tài liệu, viết script, chuẩn bị ca kiểm và rà mã.\
   Tôi đối chiếu thời lượng và dữ liệu đầu vào với nguồn, rồi dùng validator độc lập để kiểm kỹ năng, khung giờ, giờ nghỉ và số người trực tối thiểu trên các ca kỹ thuật. [Khai báo dùng AI](../docs/ai-usage.md) · [Kết quả đối chứng](../eval/l2-comparison-3.csv)\
   Khi rà bản demo do Codex hỗ trợ chuẩn bị, tôi thấy việc chạy script trước rồi mở web làm mờ thao tác của trưởng ca. Tôi yêu cầu chuyển sang luồng trưởng ca nhập và gửi prompt, sau đó hệ thống mới lập và hiển thị bản nháp. [PR #20](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/20)

3. **Một câu thử trượt của nhóm và bài học**

   Ở câu B04 của lượt 1, đề bài yêu cầu bố trí một lượt nghỉ 30 phút cho mỗi người trong ca có ba điều dưỡng. Model yêu cầu mã điều dưỡng và danh sách công việc nên chưa đưa ra giờ nghỉ, và câu được chấm `pass=0`. [Kết quả lượt 1](../eval/run-1.csv)\
   Phương án kỳ vọng là xếp ba lượt nghỉ lệch nhau để luôn có ít nhất hai người trực. Tên cụ thể có thể xác nhận sau khi trưởng ca xem bản nháp, còn mức trực tối thiểu phải được giữ ngay trong đề xuất. [Bộ câu thử](../eval/benchmark.csv)\
   Bài học tôi rút ra là cần phân biệt dữ kiện quyết định tính khả thi với chi tiết có thể xác nhận khi duyệt. Với L2, tôi biểu diễn giờ nghỉ và mức trực tối thiểu thành ràng buộc và dùng validator kiểm lại trên từng bản nháp. [Mô hình L2](../codebase/cp_sat_engine.py) · [Validator](../codebase/planning.py)
