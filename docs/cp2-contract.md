# Contract CP2 — phần dữ liệu và kiểm kế hoạch của Lam

Contract cho một lần lập kế hoạch đầu ca, dựa trên [kiến trúc](solution-design.md) và [từ điển dữ liệu](feature-spec.md) của Khoa.

## Dữ liệu và đơn vị

Đầu vào của engine là một JSON object. Ví dụ chạy được:
`data/cp2-cases.json`, trường `input` của case đầu tiên. Không truyền witness vào
model; runtime không đọc case ID hoặc benchmark.

| Thực thể | Trường runtime CP2 |
|---|---|
| shift | shift_id, ward_id, shift_length_min, coverage_rules, break_policy, room_switch_min |
| nurse | nurse_id, skills (list), available_from/to, max_capacity_min, home_zone |
| patient | patient_id, room, zone |
| task | task_id, patient_id, task_type, required_skill (list), est_duration_min, duration_source, earliest_start, deadline, mandatory=true |
| request | action=plan; yêu cầu override_safety hoặc action khác bị từ chối |

Trong JSON một ca, nurse kế thừa shift_id và patient kế thừa ward_id. Nếu dòng con mang khóa riêng, khóa phải khớp. duration_source là metadata tùy chọn của fixture. Tất cả thời gian là phút nguyên từ đầu ca;
interval [start,end), deadline = hoàn thành muộn nhất. CP2 tối đa 1440 phút/ca.
Nurse vắng được loại khỏi roster; không tự suy ra kỹ năng từ thâm niên/tuổi.
Capacity là phút công việc tối đa đã cho, tính task + transition, không trừ nghỉ
lần nữa. Duration giữ nguyên đầu vào; chưa dùng lookup hoặc dự đoán phút.

`required_skill_level` nếu được cung cấp phải có `qualification_level` cho mọi
nurse và kiểm mức đáp ứng. Các feature huấn luyện như experience, acuity, ADL,
census không có trong fixture được ghi N/A, không bịa giá trị. Đây là tập con
runtime để đi hết luồng CP2; feature-spec đầy đủ vẫn là yêu cầu khảo sát dữ liệu
cho L3, không đồng nghĩa tất cả có dữ liệu huấn luyện.

## Ràng buộc và trạng thái

- Tất cả task CP2 bắt buộc, giao đúng một lần; đúng skill/level, zone cố định,
  duration, time window, availability, capacity; không chồng task/travel/break.
- coverage_rules: start/end, zone, required_skill (null = mọi skill), min_staff.
  Đếm người trong availability, home_zone đúng, đủ skill, không nghỉ; người
  đang làm task vẫn được đếm. Không có ý nghĩa số người rảnh hoặc coverage
  lâm sàng đã được bệnh viện phê duyệt. Muốn giữ người rảnh cần rule riêng CP3.
- Break bắt buộc: mỗi nurse một block theo duration_min và window đã cho.
  Không tự nới coverage/nghỉ khi không xếp được. Block work trước/sau break là
  phase đơn giản CP2; không triển khai phase optimizer riêng.
- Overhead: room_switch_min giữa task liên tiếp khác phòng, đặt ngay trước
  task sau, không đè break/task; vẫn tính nếu đổi phòng qua break. Không tính
  chuyến đầu/cuối, setup/thiết bị, hoặc lấy thời gian hành chính làm lãng phí.
- Ràng buộc precedence, equipment hoặc synchronization có giá trị được báo
  need_info để review vì CP2 chưa hỗ trợ; không âm thầm bỏ qua rồi xác nhận lịch.
- `draft`: đã qua validator và approval_required=true; `need_info`: thiếu input;
  `infeasible`: có chứng cứ trực tiếp không nurse nào đáp ứng task bắt buộc;
  `unknown`: heuristic không tìm ra/validator bác lịch, chưa chứng minh vô nghiệm;
  `refused`: action ngoài quyền. Mọi trạng thái giữ approval_required=true.

Output JSON string có status, mode=cp2, warnings; draft thêm assignments,
breaks, unassigned_tasks=[], validation, metrics, explanation. Không gửi/sửa dữ
liệu ngoài ứng dụng. Validator tính lại từ input; không tin validation/metrics
của model. Lỗi kỹ thuật để harness ghi, không biến thành thành công.

## Tích hợp CP2 và phần bàn giao

Luồng hiện tại: JSON → kiểm dữ liệu/duration → heuristic tạo nháp → validator →
trả lịch hoặc đường lui. Heuristic đơn giản: nghỉ luân phiên, gán task theo
window/phòng/tải, ưu tiên cùng phòng khi nhiều phòng. Tham số ưu tiên 30 chỉ là
trọng số kỹ thuật cố định, không phải phút overhead hay đại lượng lâm sàng.
Không bảo đảm tối ưu; thất bại trả unknown, không nhận là infeasible.

`call_model` vẫn dùng nhánh fake của khung (1 lần, token 0); chưa có AI API tại
CP2 theo guide. Không dùng lời trả placeholder để quyết định lịch. Khoa thay
điều phối LLM và `solve_allocation` bằng CP-SAT ở CP3; giữ `validate_plan` và
hợp đồng output. Request text hiện chỉ là thông tin mô tả, không được thi hành;
chưa có bộ hiểu hội thoại/injection guard bằng LLM. Luồng không dùng ID case.

Gọi lại action=plan với input cập nhật để chỉnh bản nháp trước khi áp dụng.
Việc lập lại giữa ca cần locked/completed/in-progress tasks; chưa triển khai.

## Căn cứ chọn đầu vào

MatchRN cung cấp nhân lực cấp ca. Các bảng MIMIC mà Kiên khảo sát cung cấp thời điểm sự kiện. Cả hai chưa xác nhận số phút một điều dưỡng trực tiếp làm từng task. McGill cung cấp điểm workload theo thứ bậc. CP2 giữ thời lượng được cung cấp, thiếu thì yêu cầu bổ sung. Các mục acuity, ADL, experience và priority thuộc schema đầy đủ của Khoa. Trong fixture một ca, kỹ năng, duration, cửa giờ và coverage là các đầu vào dùng để kiểm lịch. [Data card](../data/DATA_CARD.md) · [Kết quả kiểm engine](../eval/README.md)

Ba instance UHHC đã đối chiếu (i-116, i-134, i-100) có lần lượt 4/3/5 người chăm sóc, 10/15/25 bệnh nhân và 13/17/35 dịch vụ. Đây là các instance sinh cho chăm sóc tại nhà, chỉ dùng tham khảo cấu trúc time window, di chuyển và nghỉ. [Nguồn UHHC](https://github.com/iolab-uniud/uhhc)
