# Data card — NurseFlow CP2

| Nguồn | Đơn vị và xử lý | Sử dụng trong CP2 |
|---|---|---|
| [MatchRN v1.0.0](https://zenodo.org/records/15248072), dữ liệu 2018 | 1.962 bản ghi khảo sát, 62 cột. Đối chiếu MD5 của CSV, codebook và readme. Đếm overtime trên các giá trị hợp lệ. Trích 5 bộ staffing khác nhau đầu tiên, bỏ ID, tuổi và thời điểm. | Bằng chứng áp lực trong ca. B13–B15 dùng các dòng dữ liệu 1, 2, 3. F11–F15 dùng 5 trích để kiểm đầu vào thiếu roster và task. |
| [MIMIC-IV Clinical Demo 2.2](https://physionet.org/content/mimic-iv-demo/2.2/) và [ED Demo 2.2](https://physionet.org/content/mimic-iv-ed-demo/2.2/), Johnson và cộng sự | Đọc header, đếm dòng và đối chiếu khóa trên dữ liệu PhysioNet theo nghiên cứu của Kiên. Chỉ giữ số tổng hợp. | B16–B18 kiểm giới hạn của thời điểm ghi thuốc, khoảng thủ thuật và lượt ED khi lập kế hoạch đầu ca. |
| Fixture kỹ thuật của Lam | F01–F10 sinh xác định bằng `data/build_cp2.py`, không dùng số ngẫu nhiên. Mã kỹ năng A/B/Z, ca 120 phút, capacity 105, nghỉ 15 và đổi phòng 2 phút là giả định kỹ thuật. | Kiểm lập lịch, validator, cân bằng tải, đổi phòng, nghỉ và từ chối yêu cầu vượt quyền. |

**Quyền sử dụng.** MatchRN do Martins, Musy và Simon công bố. Metadata ghi CC BY 4.0, readme ghi CC BY-NC 4.0. Nhóm ghi nguồn và sử dụng trong phạm vi học tập phi thương mại. Hai bản MIMIC Demo do PhysioNet công bố theo ODbL 1.0. Repo chỉ lưu thống kê, tham chiếu nguồn và fixture.

**Quyết định theo schema của Khoa.** L2 nhận thời lượng task đã cung cấp. Với L3, các nguồn đã kiểm chưa cho phép gán số phút điều dưỡng trực tiếp làm từng task một cách đáng tin cậy. CP2 yêu cầu bổ sung khi thiếu thời lượng. Không có tập train/test hoặc kết quả huấn luyện. McGill cung cấp thang điểm workload, UHHC cung cấp ví dụ về cấu trúc lịch chăm sóc tại nhà. Các nguồn này chỉ dùng để đối chiếu. [Phân tích dữ liệu](../evidence/data-mining.md) · [Contract](../docs/cp2-contract.md)
