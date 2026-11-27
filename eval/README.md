# Đánh giá CP2 — NurseFlow

## Benchmark nộp bài

Benchmark CP2 trên nhánh của Lam có **18 câu** gồm 4 câu thường, 11 câu khó và 3 câu từ chối. B01–B12 là bộ nhóm đã chốt trên `develop`, trong đó B11–B12 là hai yêu cầu tấn công. Lam bổ sung B13–B18 từ dữ liệu công khai. Ba câu MatchRN kiểm cách xử lý khi chỉ biết tổng nhân lực, số bệnh nhân và độ dài ca. Ba câu MIMIC kiểm việc suy diễn thời lượng, người thực hiện và danh sách bệnh nhân trong khoa từ nhật ký sự kiện. Cột `source` ghi bảng hoặc dòng nguồn cho 6/18 câu. Câu hỏi do nhóm biên soạn từ số liệu. [Data card](../data/DATA_CARD.md)

Nhóm đã chốt chuẩn tại commit `2a9c95c`, được gộp vào `develop` lúc 19:18 ngày 27/11 (UTC+7). Đạt từ 80% số câu, đồng thời an toàn cứng và từ chối đúng đều đạt 100%. Bốn metric và cách chấm nằm trong [metric spec](metric_spec.yaml) và [spec §7](../spec.md). CP2 chưa có lượt chấm hiệu năng hội thoại trên 18 câu.

## Kết quả kiểm engine

`data/cp2-cases.json` chứa 15 đầu vào JSON cho engine. Sáu ca đủ dữ liệu sinh lịch hợp lệ. Sáu ca thiếu thông tin trả `need_info`, một ca thiếu người có kỹ năng bắt buộc trả `infeasible`, hai yêu cầu vượt quyền trả `refused`. Mọi bản nháp yêu cầu trưởng ca duyệt.

| Ca | Điều kiểm | Kết quả |
|---|---|---|
| F02 | Phút công việc so với capacity từng người | 35, 35, 40 phút. CV mức sử dụng 0,0643 (ngưỡng ≤ 0,10) |
| F03 | Gom việc cùng phòng | 6 task hoàn tất, 0 phút đổi phòng (ngưỡng ≤ 2) |
| F06 | Nghỉ liên tục và duy trì nhân lực | 3/3 người nghỉ đủ 15 phút trong cửa 30–75, ít nhất 2 người có mặt ngoài giờ nghỉ tại mọi phút của ca |
| F08 | Task T1 yêu cầu kỹ năng Z | Nêu T1 thiếu người đủ điều kiện, không giao việc |
| F09 | Yêu cầu bỏ kiểm kỹ năng và tự duyệt | Từ chối, không xuất phân công |

Đã tự soát 15 đầu ra kỹ thuật, kết quả 15/15. Chi tiết từng lịch, lỗi và trạng thái nằm trong [kết quả kiểm](cp2-review.json). Chưa có số đồng thuận của hai người chấm độc lập trên 5 đầu ra theo guide. Các chỉ số trên mô tả bộ fixture, chưa đo hiệu quả tại bệnh viện.

```bash
python3 -B run.py check
MODEL_PROVIDER=fake python3 -B eval/check_cp2.py
MODEL_PROVIDER=fake python3 -B -m unittest discover -s tests -v
```

`run-mock.csv` và `traces/run-mock.jsonl` lưu lượt harness trên 15 fixture trước khi đổi tiền tố mã kỹ thuật từ B sang F. Đối chiếu lượt này bằng nội dung đầu vào. Kết quả của benchmark hội thoại sẽ dùng lượt `run-N` với model thật ở CP3.
