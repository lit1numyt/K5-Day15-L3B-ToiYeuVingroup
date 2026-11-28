# Tôi Yêu Vingroup — NurseFlow (lập phân công điều dưỡng theo ca)

**Track B · Y tế · L3B.** Danh sách thành viên trong [TEAMS.md](TEAMS.md).

## L2 CP-SAT cho CP3

`codebase/cp_sat_engine.py` nhận instance đã có duration, lập bản nháp bằng OR-Tools và
chỉ trả `draft` sau khi validator độc lập kiểm lại. Hỗ trợ skill/level, zone cố định,
windows/availability/capacity, travel, một block nghỉ có coverage, precedence và thiết bị
có capacity được khai báo. Phase dùng các task/windows/precedence đã cho và nghỉ riêng
từng nurse; không tự sinh phút chuẩn bị hoặc đổi workload score thành duration.

```bash
python -m pip install -r requirements.txt
python scripts/data/build_cp3_engine_cases.py
python -B -m unittest discover -s tests -v
python run.py check
python scripts/benchmark/compare_baseline.py
```

API vẫn là `tools.solve_allocation(instance)` và `planning.validate_plan(instance, plan)`.
`planning.input_issues(instance, require_duration=False)` kiểm cấu trúc trước L3, giữ kiểm
duration sai nếu đã được cung cấp. Backend solver cần OR-Tools; các lệnh kiểm cấu trúc
vẫn dùng thư viện chuẩn. CLI `run.py` hiện giữ điều phối/model fake của CP2 trong khi
L1 được tích hợp; kết quả L2 có `method="cp_sat"` và diagnostic solver. Kiểm này không thay
cho lượt đánh giá hội thoại gọi AI thật của CP3.
Script đối chứng chạy L4 của Khoa, CP-SAT và heuristic trên cùng 11 ca kỹ thuật, luôn
tính lại metrics qua oracle; mỗi lần sinh `eval/l2-comparison-N.json` và CSV mới.
L4 giữ chính sách một nurse/patient; đó không phải hard constraint của CP-SAT.

## Preliminary CP3

[Báo cáo dữ liệu và bàn giao](docs/eda-report.md) · [Data card](data/DATA_CARD.md).
Lam và Kiên thực hiện Preliminary, gồm sàng lọc nguồn, EDA, feature engineering và lựa chọn
phương án duration cho L3. Codex hỗ trợ tham vấn, lập trình và kiểm tra. Kết quả bàn giao theo contract của Khoa.

Bộ ca đầu vào dùng chung cho L1–L4 có sẵn trong
[data/preliminary](data/preliminary/README.md). Có thể dựng và kiểm bằng thư viện chuẩn.

```bash
python scripts/data/build_preliminary_handoff.py
python scripts/data/check_preliminary_handoff.py
```

Pipeline EDA cần các gói trong `requirements.txt` (đã kiểm bằng Python 3.12):

```bash
python -m pip install -r requirements.txt
python scripts/data/translate_zenodo.py
python scripts/data/harmonize_and_engineer.py
python scripts/eda/run_eda.py
python scripts/eda/compare_duration_options.py
python -B -m unittest discover -s tests -v
```

Bốn lệnh pipeline tạo các bảng, hình, báo cáo Preliminary và đối chứng thêm phương án duration.
Benchmark CP3 hiện có 20 câu, gồm B19–B20 bổ sung từ dữ liệu nghiên cứu.
[Phạm vi và cách kiểm](eval/README.md#bổ-sung-benchmark-từ-preliminary-cp3).
Bộ khung kiểm cấu trúc dùng thư viện chuẩn; backend L2 hiện tại cần OR-Tools và test data cần dependency EDA.

## Kết quả CP2

Lam phụ trách phương án dữ liệu, engine phân công và đánh giá CP2. Kiên nghiên cứu yêu cầu dữ liệu, so sánh và đề xuất hai nguồn MIMIC-IV Demo. [Phân công](TEAMS.md)

Hồ sơ nộp gồm [canvas](canvas.md), [sơ đồ và chuẩn đạt](spec.md), [data card](data/DATA_CARD.md), [benchmark](eval/benchmark.csv) và [4 metric](eval/metric_spec.yaml). Chuẩn đạt là ≥80% câu qua, đồng thời an toàn cứng và từ chối đúng đều đạt 100%.

**Thu bằng chứng pain.** Nhóm khai thác số liệu công khai theo Track B. Trong bộ MatchRN, 703/1.962 bản ghi (35,83%) báo làm thêm ít nhất 30 phút ở ca gần nhất. Chỉ số này phản ánh áp lực trong ca. [Nguồn và cách đếm](evidence/summary.md)

**Xác nhận khung chạy hết luồng.** Đã chạy `run.py` từ terminal bằng Python 3. F01 đi qua kiểm dữ liệu → lập lịch → kiểm ràng buộc → trả bản nháp đủ 3 task, 3 khung nghỉ, yêu cầu trưởng ca duyệt. F07 thiếu thời lượng T1 và trả `need_info` đúng trường. Cả hai lệnh thoát mã 0. Provider CP2 là `fake`, token vào/ra đều bằng 0. [Contract đầu ca](docs/cp2-contract.md)

[Kết quả CP2 đã lưu](eval/cp2-review.json). Các lệnh dưới kiểm nhánh hiện tại sau khi cài
requirements; kết quả đối chứng L2 được ghi thành lượt mới bằng script ở đầu README.

```bash
python3 -B run.py check
python3 -B -m unittest discover -s tests -v
```

Lệnh chạy F01 trong Bash

```bash
python3 -B -c 'import json; print(json.dumps(json.load(open("data/cp2-cases.json"))[0]["input"]))' | MODEL_PROVIDER=fake python3 -B run.py
```

Trên Windows, dùng `python` thay `python3`. Bộ benchmark tại CP2 có 18 câu hội thoại, gồm 6 câu từ dữ liệu công khai. F01–F15 kiểm riêng engine bằng đầu vào JSON. [Kết quả đánh giá](eval/README.md)

## Chạy trong 3 phút

Dùng Python 3.10 trở lên, cài `python -m pip install -r requirements.txt` cho backend L2 hiện tại. Mở terminal ở thư mục chứa `run.py`. Trên Windows, chạy `python run.py` rồi dán JSON của trường `input` trong [bộ fixture](data/cp2-cases.json) trên một dòng. Nhấn Enter để xem kết quả.

## Lệnh

| Lệnh | Chức năng |
|---|---|
| `python run.py` | Nhập dữ liệu một ca và nhận bản nháp hoặc yêu cầu bổ sung |
| `python run.py check` | Kiểm cấu trúc benchmark, metric và danh sách thành viên |
| `python scripts/benchmark/compare_baseline.py` | Chạy đối chứng kỹ thuật L2/L4 và lưu JSON/CSV mới theo số lượt |
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
