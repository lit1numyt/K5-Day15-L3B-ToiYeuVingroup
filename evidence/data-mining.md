# Phân tích dữ liệu CP2

## 1. Nguồn và cách đếm

Martins, Musy & Simon, *Nurse shift patterns, staffing and their association
with perceived workload*, MatchRN v1.0.0, dữ liệu 2018, 26 bệnh viện cấp tính
Thụy Sĩ. [Zenodo 15248072](https://zenodo.org/records/15248072).

Đơn vị là một bản ghi trả lời khảo sát điều dưỡng, không phải một task hoặc
một ca độc lập toàn khoa. Codebook định nghĩa C2.6 là overtime ca gần nhất,
đơn vị phút. Quy tắc đếm được ghi trước khi chạy trong `hypothesis.md`:
C2.6 >=30; mẫu số tất cả C2.6 hữu hạn, không âm. Không thay missing bằng 0.

Lệnh chạy lại, raw nằm ngoài repo:

```bash
python3 -B evidence/analyze_matchrn.py --cache /tmp/nurseflow-cp2-research
```

Script kiểm MD5 3 file theo metadata trước khi đọc. Đọc codebook XLSX bằng
stdlib zip/XML trong phiên nghiên cứu; tóm tắt có thể kiểm lại với codebook gốc.
Không join bằng ID/HospID để suy diễn từng người. Timestamps tuần trước có ngày
ngẫu nhiên theo codebook; không dùng làm thời điểm task.

## 2. Kết quả quan sát

1.962 dòng, 62 cột; 0 dòng trùng nguyên vẹn. C2.6 không thiếu/không hợp lệ.
**703/1.962 (35,83%)** tự báo overtime >=30 phút; trung vị 12, min 0, max 365.
Max không tự xoá vì cao: cần nguồn giải thích trước khi loại outlier.

| Biến | Đơn vị | Hợp lệ | Missing/invalid | Min / median / max |
|---|---|---:|---:|---|
| shiftlength | giờ | 1962 | 0 | 4 / 8.6 / 15 |
| patients | bệnh nhân trong khoa | 1962 | 0 | 1 / 19 / 53 |
| RNs | RN chăm sóc trực tiếp | 1962 | 0 | 1 / 3 / 12 |
| other | nhân viên chăm sóc khác | 1962 | 0 | 0 / 1 / 10 |
| C2.9 | bệnh nhân người trả lời phụ trách | 1962 | 0 | 1 / 7 / 40 |
| C3.4 | NASA-TLX áp lực thời gian 1–20 | 1958 | 4 | 1 / 12 / 20 |

Số máy xuất: `matchrn-summary.json`. Không coi số bệnh nhân/RN là capacity phút,
không đổi perceived workload thành duration, không suy ra thứ tự task.

## 3. Năm trích mẫu có nguồn

Chọn 5 bộ (shiftlength, patients, RNs, other) khác nhau đầu tiên trong CSV,
chỉ lấy số hữu hạn, shift/patient/RN dương, số đếm nguyên. Row là thứ tự dòng
dữ liệu từ 1, không tính header. Không xuất ID, HospID, tuổi hoặc timestamp.

| Dòng CSV | Ca (giờ) | Bệnh nhân | RN | Nhân viên khác | Làm thêm (phút, C2.6) |
|---|---:|---:|---:|---:|---:|
| 1 | 9 | 23 | 2 | 0 | 10 |
| 2 | 9 | 13 | 3 | 3 | 40 |
| 3 | 8 | 28 | 6 | 6 | 10 |
| 4 | 9 | 28 | 2 | 0 | 2 |
| 6 | 9 | 27 | 4 | 2 | 25 |

Bảng bổ sung C2.6 từ cùng dòng để minh họa phép đếm. Trong 5 ví dụ, dòng 2 vượt ngưỡng 30 phút. Tỷ lệ báo cáo dùng toàn bộ 1.962 dòng.
Dùng ở F11–F15 để kiểm không lập lịch từ staffing tổng hợp khi thiếu roster,
skill và task. Không giả các trích mẫu là 5 ca bệnh viện độc lập hay đầy đủ.

## 4. Giới hạn và quyền dùng

Readme ghi CC-BY-NC 4.0, metadata Zenodo hiện hiển thị CC BY 4.0: ghi nhận
khác biệt, giữ attribution và chỉ dùng nghiên cứu học tập phi thương mại;
chưa kết luận quyền dùng thương mại. Không commit raw record cá nhân, chỉ
bảng tổng hợp và năm trích nhỏ đã bỏ các cột định danh/nhân khẩu học.

Kết quả vượt ngưỡng 1/3 của giả thuyết bổ sung. Đây là tín hiệu overtime,
không chứng minh pain của trưởng ca tại Việt Nam, nguyên nhân phân công kém,
hoặc NurseFlow giảm overtime. Cần nguồn thứ hai đúng vai/khoa kiểm lại. EDA
này không xác thực mô hình clinical, không có nhãn task duration để train L3.

## 5. Đối chiếu MIMIC với schema của Khoa

Trong `data_research.md`, Trần Trung Kiên so sánh dữ liệu cấp cứu với dữ liệu nội trú và ICU. Kiên đề xuất nối thông tin phân loại ở ED với các sự kiện chăm sóc để xem nguồn nào cung cấp được thời điểm, thời lượng và nhân lực cho từng task. Lam đối chiếu khóa, cột thời gian và số bản ghi trong các bảng CSV của hai bản v2.2. Bảng dưới ghi kết quả dùng cho B16–B18. [MIMIC-IV-ED Demo](https://physionet.org/content/mimic-iv-ed-demo/2.2/ed/#files-panel) · [MIMIC-IV Clinical Database Demo](https://physionet.org/content/mimic-iv-demo/2.2/)

| Bảng | Phép kiểm trên bản phát hành | Ý nghĩa đối với bài làm |
|---|---|---|
| Clinical `hosp/patients` và ED `ed/edstays` | 100 bệnh nhân trong Clinical. 222 lượt ED của 64 `subject_id` khác nhau, cả 64 có trong Clinical. 172/222 lượt có `hadm_id`. | Muốn lập danh sách đầu ca cần biết khoa và khoảng hiện diện. Chỉ nối lượt nhập viện khi có khóa phù hợp. |
| ED `ed/triage` | 222 dòng, 207 có điểm acuity (18 mức 1, 97 mức 2, 90 mức 3, 2 mức 4), 15 thiếu. | Ghép với lượt ED qua `stay_id`. Acuity lúc phân loại ở ED chỉ mô tả thời điểm đó. |
| Clinical `hosp/emar` | 35.835 dòng, có `charttime`, `scheduletime`, `storetime`, thiếu cặp bắt đầu/kết thúc thao tác. | Chênh lệch thời điểm ghi nhận chưa đo được số phút lao động trực tiếp. |
| Clinical `icu/procedureevents` | 1.468 dòng. Lọc `itemid=225792` được 65 dòng; đối chiếu `icu/d_items` cho nhãn *Invasive Ventilation*. Có `starttime`, `endtime` và `caregiver_id`. | Khoảng diễn ra sự kiện có thể bao gồm thời gian thiết bị hoạt động. Mã người ghi nhận chưa xác định đầy đủ chức danh, kỹ năng hay giờ trực. |

Tái lập phép đếm bằng `python3 -B evidence/analyze_mimic.py` khi có kết nối PhysioNet. Script đọc sáu bảng của phiên bản 2.2 và chỉ in số tổng hợp. [Mã đối chiếu](analyze_mimic.py)

**Kết luận cho L3.** Các bảng có thời điểm sự kiện, nhưng chưa xác minh được nhãn phút thao tác trực tiếp theo task. Vì vậy chưa có cơ sở báo phân phối nhãn theo loại việc, tương quan acuity–duration hay độ chính xác mô hình. Việc ghép nhiều lượt thành khoa giả lập cũng không cung cấp quan sát về nhân lực và tải thực của một ca. CP2 giữ `est_duration_min` của đầu vào và dùng các giới hạn dữ liệu này trong B16–B18.
