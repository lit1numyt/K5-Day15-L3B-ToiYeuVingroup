# NurseFlow — Báo cáo L2 CP3

## 1. Phạm vi và đầu ra

NurseFlow hỗ trợ điều dưỡng trưởng lập bản nháp phân công cho một ca nội trú. Lam và Kiên
chủ trì nghiên cứu, lựa chọn nguồn, EDA và phương án bàn giao Preliminary. Lam phụ trách
CP-SAT, validator và kiểm đối chứng. Kiên phụ trách L1, Tiệp phụ trách L3 và Khoa phụ trách
kiến trúc, contract và L4. Codex hỗ trợ tham vấn, lập trình, kiểm tra và biên tập.
[Preliminary](../docs/eda-report.md) · [Khai báo dùng AI](../docs/ai-usage.md)

L1 kiểm cấu trúc JSON, L3 giữ thời lượng được cung cấp hoặc tra Simmons khi đủ điều kiện,
L2 lập lịch và validator kiểm lại cùng instance. Đầu ra là danh sách phân công và khoảng
nghỉ theo phút từ đầu ca, kèm kiểm ràng buộc, chỉ số và yêu cầu trưởng ca duyệt. Thiếu dữ
kiện trả `need_info`. `infeasible` cần chứng cứ, còn `unknown` dùng khi chưa tìm được lịch
và chưa chứng minh vô nghiệm. [Contract và schema](../docs/module-contract.md)

| Yêu cầu thiết kế | Cách thực hiện và bằng chứng |
|---|---|
| Kỹ năng, coverage và cửa giờ | Kiểm skill/level, khu vực, thời gian có mặt, deadline, tải tối đa và coverage trong giờ nghỉ. Mọi bản nháp L2 qua validator độc lập. [Kiểm solver](../tests/test_cp_sat_engine.py) · [Kiểm validator](../tests/test_cp3_validator.py) |
| Cân bằng tải và gom việc | Ưu tiên giảm đỉnh sử dụng capacity, rồi giảm chênh lệch mức sử dụng giữa các điều dưỡng, sau đó giảm di chuyển và đổi nhóm tương thích. Validator tính riêng CV, peak, tải và số phút đổi phòng. [Mô hình](../codebase/cp_sat_engine.py) |
| Phase và nghỉ được bảo vệ | Cửa giờ và thứ tự bắt buộc biểu diễn prep/care/recovery/care/handover. Mỗi điều dưỡng có một khoảng nghỉ theo chính sách ca. Cập nhật roster, task hoặc cửa giờ tạo một lần giải trên input mới. [Ca kỹ thuật](../data/cp3-engine-cases.json) · [Kiểm chạy lại](../tests/test_cp_sat_engine.py) |
| Tích hợp với dữ liệu dùng chung và các mô-đun | P01–P03 kiểm phút được cung cấp, lookup khi thiếu phút và ca có người vắng. L4 và L2 được chấm bằng cùng validator trên cùng input. [Kiểm L3 → L2](l2-integration-check-2.json) · [Bộ ca dùng chung](../data/preliminary/README.md) |

Thiết kế vận dụng đặc tả công cụ, trace, dữ liệu kiểm có nguồn, thước đo cố định và điểm
người duyệt theo các nội dung ngày 3, 4, 6, 9 và 11. [Hướng dẫn BTC](https://github.com/VinUni-AI20k/K5-L3-Day15-AI-Product-Hackathon/blob/main/02-guide.md#phu-luc)

## 2. Đối chứng kỹ thuật

Lượt 3 chạy 11 ca tổng hợp (P01–P03, C01–C08) qua bốn phương pháp. L4 có hai cách cân
bằng theo số bệnh nhân hoặc trọng số acuity. Cả hai yêu cầu một điều dưỡng phụ trách
toàn bộ công việc của một bệnh nhân. Validator chấm lại bản nháp trên input gốc. Chỉ
lịch hợp lệ được tính CV, peak và phút di chuyển. Môi trường đo dùng Python 3.12.3,
OR-Tools 9.15.6755, seed 42, một worker và giới hạn tìm kiếm 10 giây/ca.
[Kết quả CSV](l2-comparison-3.csv) · [Input, lịch và checksum JSON](l2-comparison-3.json)

| Phương pháp | Nháp hợp lệ | Nháp không hợp lệ | Vô nghiệm có chứng cứ | Chưa tìm được lịch |
|---|---:|---:|---:|---:|
| CP-SAT | 8 | 0 | 3 | 0 |
| L4 theo số bệnh nhân | 5 | 0 | 0 | 6 |
| L4 theo trọng số acuity | 5 | 0 | 0 | 6 |
| Heuristic CP2 | 6 | 3 | 0 | 2 |

- Trong 8 lịch CP-SAT hợp lệ, solver đạt `OPTIMAL` theo mục tiêu mô hình. Validator xác
  nhận đủ 35/35 công việc và 21/21 khoảng nghỉ. C04, C06 và C08 lần lượt vô nghiệm vì
  thiếu thời gian sử dụng thiết bị, coverage xung đột với nghỉ bắt buộc và người có kỹ
  năng chỉ có mặt sau deadline. Lượt đo cục bộ ghi nhận 1,400–365,028 ms/ca.
- C02 có chuẩn bị [0, 5), chăm sóc [15, 35), bố trí nghỉ trong [60, 90), chăm sóc [105, 110)
  và bàn giao [110, 115). N2 và N3 nghỉ [60, 75), N1 nghỉ [75, 90). Coverage tối thiểu
  một người được giữ theo input của ca.
- P02 có CV 0,0372 với CP-SAT và 0,1100 với heuristic, đổi lại mất 4 phút di chuyển
  so với 0 phút. Ở P03, baseline acuity và CP-SAT có cùng CV, đỉnh sử dụng và thời gian
  di chuyển. Ba nháp heuristic không hợp lệ vi phạm giới hạn thiết bị hoặc coverage.

## 3. Kiểm tích hợp và giới hạn

[PR #12](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/12) tích hợp L2 vào
`develop`. Tại commit `ebb73c8`, 184/184 unittest và 28/28 đầu vào CLI đạt. Cả 16 bản nháp
CLI chạy CP-SAT và qua validator. Phép đo kỹ thuật tái lập đủ 44 kết quả về trạng thái,
tính hợp lệ, vi phạm và chỉ số. Lượt đối chứng gốc và phép kiểm L3 độc lập lưu revision
`d8559f7`. Kiểm CLI trên bản ghép dùng provider `fake` cho lời gọi model.

L2 lập lịch cho task gắn bệnh nhân, một điều dưỡng mỗi task, một khoảng nghỉ mỗi người
và khu vực cố định. Cửa giờ và thứ tự bắt buộc lấy từ input. Trường `priority` chưa
được tối ưu riêng. Gom nhóm giảm chuyển tiếp, thời lượng chuẩn bị chỉ được tính khi có task tương
ứng. Ca đã bắt đầu có task khóa/đang làm, nhiều khoảng nghỉ và task nhiều người cần
schema riêng. Kết quả trên dữ liệu tổng hợp chỉ mô tả chất lượng lịch của các ca đã đo.

Lượt hội thoại dùng AI thật `run-1@20261128-092154` ghi 17/20 theo nhãn đã lưu ở bản trước
khi nối CP-SAT. Lượt `run-2@20261128-095930` của Khoa ghi 14/20 với policy văn bản trực tiếp.
Luồng văn bản dùng LLM theo thiết kế demo. Lịch JSON được kiểm bằng CP-SAT và validator.
Các nhãn cần rà khi kết luận an toàn được ghi ở [báo cáo hội thoại](report.md).
[Tiêu chí CP3 của BTC](https://github.com/VinUni-AI20k/K5-L3-Day15-AI-Product-Hackathon/blob/main/02-guide.md#b3-4)

## 4. Tái lập

```bash
python -m pip install -r requirements.txt
python run.py check
python scripts/data/check_preliminary_handoff.py
python -B -m unittest discover -s tests -v
python scripts/benchmark/compare_baseline.py
```

Runner lưu CSV và JSON cho lượt đo mới theo số thứ tự. Đối chiếu trạng thái, checksum
input, ràng buộc và các chỉ số. Thời gian chạy có thể thay đổi theo môi trường.
