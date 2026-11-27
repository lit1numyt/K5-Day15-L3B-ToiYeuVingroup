# Tôi Yêu Vingroup — NurseFlow (lập phân công điều dưỡng theo ca)

**Track B · Y tế · L3B.** Danh sách thành viên trong [TEAMS.md](TEAMS.md).

## Kết quả CP2

Lam phụ trách phương án dữ liệu, engine phân công và đánh giá CP2. Kiên nghiên cứu yêu cầu dữ liệu, so sánh và đề xuất hai nguồn MIMIC-IV Demo. [Phân công](TEAMS.md)

Hồ sơ nộp gồm [canvas](canvas.md), [sơ đồ và chuẩn đạt](spec.md), [data card](data/DATA_CARD.md), [benchmark](eval/benchmark.csv) và [4 metric](eval/metric_spec.yaml). Chuẩn đạt là ≥80% câu qua, đồng thời an toàn cứng và từ chối đúng đều đạt 100%.

**Thu bằng chứng pain.** Nhóm khai thác số liệu công khai theo Track B. Trong bộ MatchRN, 703/1.962 bản ghi (35,83%) báo làm thêm ít nhất 30 phút ở ca gần nhất. Chỉ số này phản ánh áp lực trong ca. [Nguồn và cách đếm](evidence/summary.md)

**Xác nhận khung chạy hết luồng.** Đã chạy `run.py` từ terminal bằng Python 3. F01 đi qua kiểm dữ liệu → lập lịch → kiểm ràng buộc → trả bản nháp đủ 3 task, 3 khung nghỉ, yêu cầu trưởng ca duyệt. F07 thiếu thời lượng T1 và trả `need_info` đúng trường. Cả hai lệnh thoát mã 0. Provider CP2 là `fake`, token vào/ra đều bằng 0. [Contract đầu ca](docs/cp2-contract.md)

```bash
python3 -B run.py check
MODEL_PROVIDER=fake python3 -B eval/check_cp2.py
python3 -B -m unittest discover -s tests -v
```

Lệnh chạy F01 trong Bash

```bash
python3 -B -c 'import json; print(json.dumps(json.load(open("data/cp2-cases.json"))[0]["input"]))' | MODEL_PROVIDER=fake python3 -B run.py
```

Trên Windows, dùng `python` thay `python3`. Bộ benchmark có 18 câu hội thoại, gồm 6 câu từ dữ liệu công khai. F01–F15 kiểm riêng engine bằng đầu vào JSON. [Kết quả đánh giá](eval/README.md)

## Chạy trong 3 phút

Dùng Python 3.10 trở lên và thư viện chuẩn. Mở terminal ở thư mục chứa `run.py`. Trên Windows, chạy `python run.py` rồi dán JSON của trường `input` trong [bộ fixture](data/cp2-cases.json) trên một dòng. Nhấn Enter để xem kết quả.

## Lệnh

| Lệnh | Chức năng |
|---|---|
| `python run.py` | Nhập dữ liệu một ca và nhận bản nháp hoặc yêu cầu bổ sung |
| `python run.py check` | Kiểm cấu trúc benchmark, metric và danh sách thành viên |
| `python eval/check_cp2.py` | Chấm 15 fixture và ghi kết quả vào `eval/cp2-review.json` |
| `python run.py eval` | Chạy benchmark qua harness. Từ CP3, lượt dùng model thật được ghi vào `eval/run-N.csv` |
| `python run.py score eval/run-N.csv` | Tổng hợp điểm của lượt đã chấm |
| `python run.py simulate` | Chạy mô phỏng chi phí cho giai đoạn đo sản phẩm |

## Phần nào thật, phần nào giả

| Thành phần | Trạng thái tại CP2 |
|---|---|
| Lập lịch và kiểm ràng buộc | Chạy trên JSON đầu ca, trả bản nháp để trưởng ca duyệt |
| Lời gọi model | Dùng provider `fake` theo khung CP2. Phần hội thoại qua API thuộc CP3 |

## Dùng AI vào việc gì

Codex hỗ trợ Lam đối chiếu nguồn dữ liệu, viết mã lập lịch và kiểm kết quả CP2. Phần đóng góp và cách kiểm ghi trong [khai báo dùng AI](docs/ai-usage.md).

## Bảy hạng mục bắt buộc — nằm ở file nào

| # | Hạng mục | File |
|---|---|---|
| 1 | Bằng chứng pain | `evidence/` (tổng hợp ở `evidence/summary.md`) |
| 2 | Impact có số | `spec.md` §2 |
| 3 | Thiết kế giải pháp | `spec.md` §4 |
| 4 | Bản chạy thử làm trọn lát cắt | `codebase/` · lệnh ở mục "Lệnh" |
| 5 | Định nghĩa "tốt" + bộ câu thử | `data/DATA_CARD.md` · `eval/` |
| 6 | Mô phỏng chi phí khi dùng thật | `cost/` |
| 7 | Slide + demo + video dự phòng (CP4) | [Dàn ý](slides/outline.md) |
| + | *Bonus:* người dùng thử | `validation/log.md` |
