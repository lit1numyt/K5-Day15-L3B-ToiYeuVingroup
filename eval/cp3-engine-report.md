# NurseFlow — Báo cáo L2 CP3

## 1. Phạm vi và phương pháp

Lam phụ trách L2 CP-SAT, validator và đánh giá kỹ thuật theo kiến trúc của Khoa. Lam và
Kiên thực hiện nghiên cứu, lựa chọn phương án và chuẩn bị dữ liệu Preliminary. Bản tích hợp
dùng `develop=d6b1b9c`, gồm L3 của Tiệp tại `cd8e95a` và L4 của Khoa tại `f93a719`.
Codex hỗ trợ tham vấn, lập trình, kiểm tra và biên tập.

L2 nhận duration đã có, giữ đơn vị phút nguyên và trả bản nháp chờ trưởng ca duyệt.
Mô hình kiểm skill/level, zone cố định, availability, cửa giờ, capacity, travel giữa hai
task liên tiếp, một block nghỉ có coverage, precedence và capacity thiết bị đã khai báo.
Coverage giữ nghĩa của contract: nhân sự có mặt đúng zone/skill và không nghỉ; không
phải số người rảnh. Capacity tính task và travel, không trừ break lần nữa.

Phase được biểu diễn bằng task chuẩn bị/chăm sóc/bàn giao có windows và precedence;
recovery là khoảng nghỉ của từng nurse. C02 kiểm prep → care → recovery → care → handover.
L2 không tự sinh task, thời lượng chuẩn bị hoặc đổi taxonomy weight thành phút.
Re-solve dùng snapshot input mới trước khi bản nháp được áp dụng.

Mục tiêu CP-SAT ưu tiên peak utilization làm tròn lên theo phần nghìn, tiếp đến tổng độ
lệch utilization giữa các cặp nurse, sau cùng travel và số lần đổi nhóm tương thích.
Hệ số được suy từ cận horizon/số nurse/task để giữ thứ tự ưu tiên. Đây là mục tiêu kỹ thuật;
CV được validator tính lại, không nhận mục tiêu tuyến tính là tối ưu chính xác CV.
Cấu hình: Python 3.12.3, OR-Tools 9.15.6755, seed 42, một worker, giới hạn 10 giây/ca.
FEASIBLE chưa chứng minh optimal; hết giờ chưa có lịch trả unknown; infeasible cần chứng cứ.

Phương pháp vận dụng các nền tảng BTC dẫn chiếu: đặc tả công cụ (ngày 3), trace (ngày 4),
provenance và dữ liệu kiểm (ngày 6), đánh giá có thước đo cố định (ngày 9), người duyệt
(ngày 11). Trong L2, các nguyên tắc này thể hiện qua tool contract, oracle độc lập,
fixture có nguồn/giả định, lưu cả kết quả thất bại và `approval_required=true`.
[Bản đồ kiến thức của BTC](https://github.com/VinUni-AI20k/K5-L3-Day15-AI-Product-Hackathon/blob/main/02-guide.md#phu-luc).

## 2. Bộ kiểm và cách chấm

Lượt [l2-comparison-3.csv](l2-comparison-3.csv) và [JSON chi tiết](l2-comparison-3.json)
chạy 11 ca × 4 phương pháp. P01–P03 là bộ ca shared; C01–C08 bổ sung tình huống nghỉ,
phase, resource, kỹ năng, travel và vô nghiệm. Các ca đều synthetic có provenance,
không phải dữ liệu người bệnh thực hoặc bằng chứng pain.
[Ca và cách sinh](../data/cp3-engine-cases.json) · [Mã sinh](../scripts/data/build_cp3_engine_cases.py).

Mỗi allocator nhận bản sao cùng input. Validator chấm lại trên bản gốc, bỏ metrics tự khai;
lịch invalid không được chấm CV/peak/overhead. JSON lưu đầy đủ input, output, thời gian,
revision `d8559f7` và checksum source. Mỗi lần chạy tạo số lượt mới.

L4 có hai baseline: cân bằng số patient và cân bằng tổng workload_weight theo taxonomy
(acuity-weighted). Cả hai giữ toàn bộ task của một patient cho cùng nurse, chặt hơn phân
task của L2. Phép so phản ánh các chính sách hiện tại trên bộ ca này, chưa chứng minh
ưu thế của một thuật toán trên mọi khoa hoặc khi ép cùng chính sách continuity.
Đã hỗ trợ sửa hẹp trạng thái baseline: chỉ thất bại continuity thì unknown, không nhận
là bài toán chung vô nghiệm. Thuật toán phân theo patient và mô hình taxonomy được giữ.

## 3. Kết quả

| Phương pháp | Draft hợp lệ | Draft invalid | Infeasible | Unknown |
|---|---:|---:|---:|---:|
| cp_sat | 8 | 0 | 3 | 0 |
| l4_patient_count | 5 | 0 | 0 | 6 |
| l4_patient_weight | 5 | 0 | 0 | 6 |
| cp2_heuristic | 6 | 3 | 0 | 2 |

CP-SAT trả OPTIMAL ở 8 ca có lịch hợp lệ và INFEASIBLE ở C04/C06/C08. Ba ca này lần lượt
thiếu quỹ thời gian thiết bị, coverage không cho phép nghỉ bắt buộc, và specialist không
có mặt trước deadline. Không bỏ task hoặc giảm coverage để tạo nghiệm.
C01 có nghỉ khả thi khi bố trí hai người nghỉ đồng thời; heuristic/baseline nghỉ tuần tự
không tìm được lịch. C05 cần tách hai kỹ năng của một patient cho hai nurse, nên baseline
continuity không tìm được phân công. Trên 8 ca có lịch, CP-SAT phân đủ 35/35 task và
bố trí đủ 21/21 block nghỉ; oracle không phát hiện vi phạm coverage, kỹ năng hoặc deadline.
Ba ca vô nghiệm vẫn được giữ nguyên trong lượt đo.

| Ca | Phương pháp | CV utilization | Peak utilization | Travel (phút) |
|---|---|---:|---:|---:|
| P01 | l4_patient_count | 0.0000 | 0.2095 | 6 |
| P01 | l4_patient_weight | 0.0442 | 0.2095 | 4 |
| P01 | cp_sat | 0.0000 | 0.1905 | 0 |
| P01 | cp2_heuristic | 0.0000 | 0.1905 | 0 |
| P02 | l4_patient_count | 0.3021 | 0.1810 | 6 |
| P02 | l4_patient_weight | 0.1622 | 0.1429 | 4 |
| P02 | cp_sat | 0.0372 | 0.1238 | 4 |
| P02 | cp2_heuristic | 0.1100 | 0.1238 | 0 |
| P03 | l4_patient_count | 0.1429 | 0.2286 | 8 |
| P03 | l4_patient_weight | 0.0000 | 0.1810 | 4 |
| P03 | cp_sat | 0.0000 | 0.1810 | 4 |
| P03 | cp2_heuristic | 0.2778 | 0.2190 | 2 |

P02 cho thấy trade-off: CP-SAT có CV thấp hơn heuristic, nhưng travel là 4 thay vì 0 phút.
Ở P03, baseline acuity-weighted đạt cùng CV/peak/travel với CP-SAT; baseline count cũng
có CV thấp hơn heuristic. Báo cáo giữ mọi ca và mọi metric,
không chọn riêng chỉ số thuận lợi. Heuristic có ba draft invalid ở C03/C04/C06 vì chưa mô
hình hóa đầy đủ resource/coverage; các draft đó được oracle phát hiện và không tính metrics.
Thời gian CP-SAT của lượt này từ 1.400 đến 365.028 ms/ca,
đo trên môi trường local gồm cả dựng mô hình và kiểm lại. Đây là một lượt đo, không phải
cam kết latency cho dữ liệu ward thực hoặc cho LLM.

## 4. Kiểm chứng, tích hợp và giới hạn

Đối chiếu phần Lam với [kiến trúc](../docs/solution-design.md) và
[module contract](../docs/module-contract.md):

| Yêu cầu | Đầu ra đã thực hiện | Bằng chứng |
|---|---|---|
| CP-SAT là công cụ L2, giữ seam cho L1 | `solve_allocation(instance) -> plan`, có diagnostic solver; không tự áp dụng | [Solver và tool](../tests/test_cp_sat_engine.py) |
| Kỹ năng/level, zone, thời gian, capacity, coverage | Draft thỏa các ràng buộc khai báo; không bỏ task hoặc nới luật khi vô nghiệm | [Oracle tính tay](../tests/test_planning.py), C04/C06/C08 |
| Phút đầu vào có căn cứ, tách vai trò L3 | Kiểm trước/sau L3, giữ phút đã cho, không đổi điểm taxonomy thành phút | [Kiểm tích hợp](../tests/test_workload_integration.py) |
| Gom việc và phase có giờ nghỉ | Giảm đổi phòng/nhóm; task prep/care/handover theo windows/precedence và một break mỗi nurse | [Kiểm grouping](../tests/test_cp_sat_engine.py), timeline C02 bên dưới |
| Chạy lại bản nháp theo yêu cầu | Giải snapshot mới sau khi đổi roster/task/window, giữ nguyên input | [Kiểm re-solve](../tests/test_cp_sat_engine.py) |
| Validator và metrics độc lập | Kiểm lại task/travel/break, precedence và thiết bị; bác metrics tự khai của plan | [Oracle mở rộng](../tests/test_cp3_validator.py), [kiểm phép so](../tests/test_compare_baseline.py) |
| Đối chứng và hồ sơ trung thực | Hai baseline L4, CP-SAT, heuristic trên cùng input; giữ invalid/unknown/infeasible và output cũ | [44 kết quả](l2-comparison-3.csv), [chi tiết](l2-comparison-3.json) |

Các mở rộng precedence/equipment và nghĩa `infeasible` được ghi rõ trên nhánh L2 để Khoa
review giao diện khi tích hợp; chưa coi là thay đổi đã được Khoa phê duyệt.

Timeline C02 từ lượt đo, đơn vị phút từ đầu ca:

| Hoạt động | Nurse | Khoảng thực hiện |
|---|---|---|
| T1 · preparation | N3 | [0, 5) |
| T2 · care | N2 | [15, 35) |
| Recovery theo policy | N2, N3 | [60, 75) |
| Recovery theo policy | N1 | [75, 90) |
| T3 · care | N1 | [105, 110) |
| T4 · handover | N3 | [110, 115) |

Mỗi nurse có 15 phút nghỉ theo input; coverage tối thiểu một người được giữ. Đây là ca
kỹ thuật gắn patient, không phải chính sách nghỉ lâm sàng hoặc thời lượng nghỉ chung cả khoa.

- Bộ unittest trên bản tích hợp L1–L4 đạt 184/184, gồm hồi quy CP2, input/oracle CP3, CP-SAT,
  gom task theo compat_group_key/thiết bị, giữ nguyên input, đổi roster/task/window khi
  re-solve, hai baseline L4, L3 và phép so có metrics giả.
- P01–P03 và F01–F06 có lịch hợp lệ; F02/F03 giữ quality anchors. F08 thiếu người có
  kỹ năng cần thiết nên infeasible. CLI chạy hết 28 input, gồm hỏi lại/từ chối và chạy lại
  bản nháp với roster/task/window mới. Luồng JSON trên bản tích hợp PR #11 được
  kiểm lại với L1/L3 và CP-SAT, dùng provider `fake` để kiểm cục bộ.
- [Kiểm tích hợp mới](l2-integration-check-2.json) chạy ngay trên bản tích hợp `d8559f7`:
  P01–P03 qua L3 → CP-SAT thật → validator, giữ nguyên input, duration khớp dữ liệu shared.
  Task toileting thiếu staffing được L3 hỏi lại và không chuyển bản thiếu dữ kiện sang solver.
  Đoạn mẫu tích hợp trong tài liệu L3 đã được chạy với P01–P03 và ca duration sai; dùng
  `input_issues(require_duration=False)` trực tiếp, không lọc thông báo lỗi theo chuỗi.
  L3 dùng given/lookup Simmons theo quyết định Preliminary; thực nghiệm ML phòng mổ của
  Tiệp nằm riêng trong [báo cáo L3](../docs/l3-workload-estimator.md). Đây chưa phải luồng L1/LLM.
- B01–B18, metric/spec §7, framework và output lịch sử giữ nguyên. Kết quả engine không
  thay tỷ lệ đạt của benchmark hội thoại hoặc lượt gọi AI thật.
- Bản sao mã nguồn sạch chạy đủ unittest, kiểm benchmark, kiểm Preliminary và phép so;
  tái lập đủ 44 kết quả về trạng thái, tính hợp lệ và metrics.

Chưa hỗ trợ task chung khoa không gắn patient, task nhiều staff đồng bộ, nhiều block nghỉ
hoặc re-solve giữa ca có task đã hoàn tất/đang làm. Phạm vi là bản nháp đầu ca theo schema
đã ghi trong contract; trạng thái/locked và các ràng buộc chưa có schema cần được làm rõ.
Taxonomy synthetic/lookup chưa được hiệu chỉnh
bằng dữ liệu patient-task nội trú liên kết. Khoảng trống trên lịch không tự được tính là
nghỉ được bảo vệ. Không nhận số liệu này là cải thiện lâm sàng hoặc pain đã được giải quyết.

[Wireframe của Khoa tại 53d3b4f](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/blob/53d3b4f/design/wireframes/README.md)
là bố cục tĩnh, chưa thay đổi contract. Ý tưởng thao tác xen kẽ/song song cần schema riêng;
L2 hiện giữ các khoảng task/travel/break của một nurse không chồng nhau. UI tích hợp cần
hiển thị output đã qua validator, không lấy các khối giờ cố định của wireframe làm lịch thực.

L1 của Kiên đã vào `main` qua [PR #11](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/11).
Lượt AI thật `run-1@20261128-092154` (17/20) thuộc bản L1 dùng heuristic CP2. Kết quả này
được bảo toàn. Bản ghép CP-SAT kiểm lại luồng JSON cục bộ. Luồng văn bản tự do vẫn
dùng bản nháp hội thoại của L1 và chưa có cùng xác minh bằng CP-SAT/validator.

## 5. Tái lập

```bash
python -m pip install -r requirements.txt
python scripts/data/build_cp3_engine_cases.py
python -B -m unittest discover -s tests -v
python run.py check
python scripts/data/check_preliminary_handoff.py
python -B -m unittest discover -s tests -p test_workload_integration.py -v
python scripts/benchmark/compare_baseline.py
```

Báo cáo sử dụng lượt đo 3 và kiểm tích hợp mới được liên kết ở trên.

Lượt mới có thể khác thời gian hoặc chọn lịch tương đương khi có nhiều nghiệm. Đối chiếu
source checksum, trạng thái, ràng buộc và metric thay vì yêu cầu mọi timestamp giống nhau.
