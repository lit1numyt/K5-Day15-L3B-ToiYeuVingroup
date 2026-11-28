# Data card — NurseFlow

## Preliminary CP3

Lam và Kiên phụ trách lựa chọn nguồn và chuẩn bị dữ liệu phục vụ L3 theo kiến trúc của Khoa.
Phiên bản nguồn, checksum, ngày kiểm và mức truy cập được ghi trong catalogue.
[Catalogue nguồn](reference/preliminary_sources.json).

| Dataset | Nguồn, xử lý và số lượng | Mục đích và giới hạn |
|---|---|---|
| Zenodo 20754938 v1, Hara, quan sát tháng 7/2024 | XLSX MD5 `78e04eb6c4ffcf2b599afd3080f97c21`. Dịch nhãn, bỏ một dòng trùng, xử lý qua 0h và gộp cùng hoạt động liên tục. 11.074 dòng raw → 11.073 segment → 2.380 episode của 37 staff/168 staff-shift. | EDA và kiểm duration hoạt động OR. Thiếu liên kết patient, acuity/ADL và experience. |
| Feature từ Zenodo | 2.192 episode làm việc × 10 cột. Target là actual_duration_min. Chọn task_name cho tra median, task_category và nurseflow_task_type phục vụ tổng hợp/đối chứng. Chia 5 folds theo staff, fit encoder và thống kê trên train. | ID/ngày/dòng Excel phục vụ truy nguồn và chia tập. Mỗi tên xác định một category và một nhóm task trong nguồn. |
| Simmons et al., DOI 10.1111/jgs.19507, Table 3 | Chín dòng mean/SD/min/max phút mỗi patient episode tại khoa ACE. Giữ số thập phân gốc và metadata trong reference/ward_task_duration.csv. | Tham chiếu lookup L3 nội trú. Bốn tên khớp các ví dụ task ở feature-spec. Cần đối chiếu mô tả việc và staffing. Toileting/mobility có trường hợp cần hai staff. Chưa có hệ số acuity hoặc kiểm định tại khoa đích. |
| eICU Demo, NRP, McGill và các nguồn bổ sung | Sàng lọc và kiểm ngữ nghĩa trường theo vai trò. NRP hỗ trợ cấu trúc staffing/skill/coverage. McGill có bảng trích 113 item/22 section trong reference/mcgill_workload_items.csv, giữ ID/dòng nguồn và điểm gốc. | Bảng ghép và hệ số duration tự đặt còn thiếu căn cứ quan sát. Mức xác minh của từng nguồn ở catalogue. |

**Bộ ca tích hợp.** `preliminary/instances.json` có ba ca synthetic tạo xác định từ fixture F03,
khai báo roster, skill/level, acuity/ADL, cửa giờ, nghỉ và coverage trong metadata. Seed bằng
null vì quy trình không lấy mẫu ngẫu nhiên. Duration cho sẵn giữ giá trị kỹ thuật; duration
lookup lấy mean Simmons và làm tròn lên. Cả ba ca đã kiểm tự động qua input check và validator.
Các ca là dữ liệu kiểm giao diện, tách khỏi dữ liệu quan sát và pain evidence.
[Hướng dẫn sử dụng](preliminary/README.md).

**Nguồn và quyền sử dụng.** Zenodo CC BY 4.0, ghi attribution Hara và các bước dịch/làm sạch
của nhóm. Bảng Simmons trích số liệu tổng hợp có nguồn, bài báo CC BY-NC-ND 4.0,
giấy phép dataset raw riêng chưa được xác minh. [Zenodo](https://zenodo.org/records/20754938) · [Simmons, Table 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC12303744/) · [Giấy phép bản xuất bản](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1111/jgs.19507).

**Chất lượng dữ liệu.** Giữ số dòng Excel vật lý, mã ca gốc, missing giờ kết thúc ca và
trạng thái overtime Unspecified. Episode/nhóm task là biến dẫn xuất có quy tắc.
Số quan sát, missingness, split, sai số từng nhóm và prediction được lưu trong processed/.
Hướng L3 bàn giao là duration đã cho hoặc lookup đúng công việc, số phút nạp solver được
làm tròn lên theo quy tắc kỹ thuật. Phạm vi áp dụng và các trường còn thiếu được trình bày
trong báo cáo. [Báo cáo EDA và feature](../docs/eda-report.md).

**Câu thử từ dữ liệu.** B19 dùng nhãn chuẩn bị thuốc và median từ Zenodo, B20 dùng số phút
mobility và footnote staffing trong Simmons. Các tình huống được nhóm viết để kiểm xác nhận
đúng loại việc và điều kiện áp dụng. [Bộ câu thử](../eval/benchmark.csv).

**Tái lập.** Cài dependency rồi chạy bốn script theo README.
[Hướng dẫn chạy](../README.md#preliminary-cp3).

## Ca kỹ thuật L2 CP3

`cp3-engine-cases.json` có tám ca synthetic tạo xác định từ P01 bằng
`scripts/data/build_cp3_engine_cases.py`, seed null, kèm checksum nguồn. Các giá trị
duration, staffing, skill, windows, coverage và capacity thiết bị là giả định kỹ thuật.
Các ca kiểm nghỉ song song có coverage, phase/precedence, thiết bị chia sẻ, skill tách,
travel qua break và trường hợp vô nghiệm. Chúng không phải dữ liệu bệnh viện quan sát
hoặc bằng chứng pain; tách khỏi benchmark hội thoại và output lịch sử.

## Hồ sơ CP2 được giữ nguyên

| Nguồn | Đơn vị và xử lý | Sử dụng trong CP2 |
|---|---|---|
| [MatchRN v1.0.0](https://zenodo.org/records/15248072), dữ liệu 2018 | 1.962 bản ghi khảo sát, 62 cột. Đối chiếu MD5 của CSV, codebook và readme. Đếm overtime trên các giá trị hợp lệ. Trích 5 bộ staffing khác nhau đầu tiên, bỏ ID, tuổi và thời điểm. | Bằng chứng áp lực trong ca. B13–B15 dùng các dòng dữ liệu 1, 2, 3. F11–F15 dùng 5 trích để kiểm đầu vào thiếu roster và task. |
| [MIMIC-IV Clinical Demo 2.2](https://physionet.org/content/mimic-iv-demo/2.2/) và [ED Demo 2.2](https://physionet.org/content/mimic-iv-ed-demo/2.2/), Johnson và cộng sự | Đọc header, đếm dòng và đối chiếu khóa trên dữ liệu PhysioNet theo nghiên cứu của Kiên. Chỉ giữ số tổng hợp. | B16–B18 kiểm giới hạn của thời điểm ghi thuốc, khoảng thủ thuật và lượt ED khi lập kế hoạch đầu ca. |
| Fixture kỹ thuật của Lam | F01–F10 sinh xác định bằng `data/build_cp2.py`, không dùng số ngẫu nhiên. Mã kỹ năng A/B/Z, ca 120 phút, capacity 105, nghỉ 15 và đổi phòng 2 phút là giả định kỹ thuật. | Kiểm lập lịch, validator, cân bằng tải, đổi phòng, nghỉ và từ chối yêu cầu vượt quyền. |

**Quyền sử dụng.** MatchRN do Martins, Musy và Simon công bố. Metadata ghi CC BY 4.0, readme ghi CC BY-NC 4.0. Nhóm ghi nguồn và sử dụng trong phạm vi học tập phi thương mại. Hai bản MIMIC Demo do PhysioNet công bố theo ODbL 1.0. Repo chỉ lưu thống kê, tham chiếu nguồn và fixture.

**Quyết định tại CP2 theo schema của Khoa.** L2 nhận thời lượng task đã cung cấp. Với L3, các nguồn đã kiểm ở CP2 chưa cho phép gán số phút điều dưỡng trực tiếp làm từng task một cách đáng tin cậy. CP2 yêu cầu bổ sung khi thiếu thời lượng. CP2 chưa có tập train/test hoặc kết quả huấn luyện. McGill cung cấp thang điểm workload, UHHC cung cấp ví dụ về cấu trúc lịch chăm sóc tại nhà. Các nguồn này chỉ dùng để đối chiếu. [Phân tích dữ liệu](../evidence/data-mining.md) · [Contract](../docs/cp2-contract.md)
