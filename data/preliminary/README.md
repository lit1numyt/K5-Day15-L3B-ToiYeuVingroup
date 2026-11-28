# Dữ liệu dùng chung cho bước build CP3

Lam và Kiên chuẩn bị bộ bàn giao theo module contract của Khoa.
Các tệp nằm trong thư mục `data/preliminary`. Hai lệnh dưới dùng thư viện chuẩn Python.

```bash
python scripts/data/build_preliminary_handoff.py
python scripts/data/check_preliminary_handoff.py
```

## Tệp và cách dùng

| Người nhận | Tệp và đầu vào sử dụng |
|---|---|
| Kiên, L1 | Đọc `instances.json`, gửi JSON của từng `case["instance"]` vào `answer`. Dùng `case["l3_input"]` để phát triển nhánh estimate trước solve. Các câu thiếu thông tin/từ chối ở benchmark B01–B20. |
| Lam, L2/validator | Gọi `solve_allocation(case["instance"])`, sau đó `validate_plan` trên cùng instance. Dữ liệu đã có phút nguyên, kỹ năng/level, coverage, availability, capacity, room và break policy. |
| Tiệp, L3 | Dùng `case["l3_input"]` làm input và `case["instance"]` làm kết quả dữ liệu mong đợi. P01 giữ phút đã cho; P02/P03 điền 5 duration thiếu từ bảng Simmons, giữ T1 bằng 10 phút. |
| Khoa, L4 | Tham khảo 113 item trong `data/reference/mcgill_workload_items.csv`. Patient có acuity_score, adl_dependency, care_category, isolation_precaution, room/zone; nurse có kỹ năng, qualification và experience. Phát triển classify_patient/baseline trên các input này rồi chấm plan bằng cùng validator. |

```python
import json
from pathlib import Path

bundle = json.loads(Path("data/preliminary/instances.json").read_text(encoding="utf-8"))
case = bundle["cases"][1]
instance = case["instance"]
l3_input = case["l3_input"]
```

P01/P02 có ba nhân viên, P03 loại N3 do vắng. Coverage tối thiểu bằng một người được
khai báo từ đầu ở cả ba ca. Các ca có sáu task, sáu patient, ba phòng, nghỉ 15 phút trong
ca 120 phút. Checker kiểm đủ bộ P01–P03, source checksum, các trường giao diện, duration
cho sẵn, cặp input L3 và tính khả thi bằng một lịch chứng minh từ heuristic qua validator.
CP-SAT và hai baseline L4 đã chạy trên cùng instance, được chấm lại bằng validator.
[Kết quả đối chứng và cách tái lập](../../eval/cp3-engine-report.md).

## Phạm vi kiểm

| Nội dung | Dữ liệu sử dụng |
|---|---|
| Schema core, phút nguyên, duration given/lookup | P01–P03; P02/P03 giữ T1 và điền năm duration còn thiếu. |
| Vắng người và giữ chính sách coverage | P03 so với P02, chỉ loại N3 khỏi roster. |
| Kỹ năng hiếm, deadline và nghỉ | Các fixture kỹ thuật CP2 F04–F08 trong [cp2-cases.json](../cp2-cases.json). |
| Yêu cầu vượt quyền, dữ liệu thiếu | F09–F15 và bộ benchmark hội thoại B01–B20. |

P01–P03 dùng cùng tập kỹ năng, level 2 cho nurse và level 1 cho task để tập trung kiểm
giao diện. Phase, equipment, preparation và precedence được kiểm thêm bằng
[C01–C08](../cp3-engine-cases.json), không nhận ba ca shared là đủ kiểm mọi tính năng.

## Nguồn và giả định

Bundle được ghi `data_kind="synthetic"`, tạo xác định từ cấu trúc F03, dùng lại ID kỹ thuật.
Roster, skill, qualification, experience, acuity/ADL, isolation, cửa giờ, coverage và nghỉ
là giả định kỹ thuật được ghi trong field_provenance. Các mức acuity/ADL là giá trị kiểm
giao diện cho taxonomy của Khoa. Quan hệ giữa các mức này với phút chăm sóc cần dữ liệu
quan sát để hiệu chỉnh. Mức ordinal của ca kỹ thuật được khai báo riêng với điểm item McGill.
Tính điểm McGill cho một patient cần các thuộc tính/đánh dấu item của patient đó.

Duration `given` giữ giá trị fixture. Duration `lookup` lấy mean nguồn Simmons và làm tròn
lên phút nguyên. Các case dùng sáu loại việc chăm sóc một người phù hợp định nghĩa bảng.
Đây là dữ liệu tích hợp có nguồn tham chiếu, phạm vi tác dụng của nó là kiểm interface và
luồng lập lịch. Bộ này được tách khỏi dữ liệu quan sát để train/eval duration và pain evidence.

Với thời lượng nội trú, tra [bảng Simmons](../reference/ward_task_duration.csv) theo điều kiện
ở [contract §3.3](../../docs/module-contract.md). Với thí nghiệm OR, dùng
[feature table](../processed/l3_activity_features.csv) và [lookup theo tên](../processed/activity_duration_lookup.csv).
Lookup OR được tính trên toàn tập sạch để tham khảo. Phép đánh giá OOF fit lookup riêng
trên train từng fold. Phạm vi OR và nội trú cần được giữ rõ khi sử dụng hai bảng.

Các nguồn đã kiểm còn thiếu raw patient-task nội trú liên kết để train/đánh giá ảnh hưởng
acuity/ADL. Bộ hiện tại cho phép triển khai nhánh given/lookup theo kiến trúc và phát triển
các module song song. [Báo cáo quyết định dữ liệu](../../docs/eda-report.md).
