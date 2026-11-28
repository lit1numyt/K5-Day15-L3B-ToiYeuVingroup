# Demo luồng NurseFlow

Một demo chạy được, nối các mảnh đã có thành một luồng lập kế hoạch ca:

```
python -m pip install -r requirements.txt
python scripts/demo/run_demo.py
```

L2 dùng OR-Tools CP-SAT. Provider lấy từ môi trường hoặc `.env` theo `.env.example`.
Để kiểm luồng cục bộ, đặt `MODEL_PROVIDER=fake`. Để đo AI thật, cấu hình provider,
model và API key rồi chạy lại. L4 dùng KMeans khi nạp được model, có rule fallback.

Luồng demo trên một ca mẫu (`data/preliminary/instances.json`, case P02):
1. **[L3] `estimate_duration`** — điền thời lượng việc còn thiếu từ bảng Simmons (gắn nhãn
   `lookup:simmons…`), giữ nguyên thời lượng đã cho (`given`).
2. **[L4] `classify_patient`** — xếp bệnh nhân thành tier nhẹ/trung bình/nặng.
3. **[Engine] `answer()`** — L2 CP-SAT lập bản nháp và `validate_plan` kiểm lại
   kỹ năng, deadline, capacity, di chuyển, nghỉ và coverage.
4. **[L4] `baseline_allocate`** — so với cách truyền thống (theo đầu bệnh nhân và acuity-weighted)
   trên cùng ca. Script in các chỉ số đo được của từng phương pháp.

Kết thúc ở trạng thái `draft` (`approval_required=true`) — AI đề xuất, trưởng ca duyệt.

## Xuất lịch ra giao diện

```bash
python scripts/demo/build_demo.py
```

Script sinh ca tổng hợp với seed 7, gồm 5 điều dưỡng, 12 bệnh nhân và 20 task.
Tên, roster, kỹ năng, acuity/ADL và phút công việc là giả định kỹ thuật để kiểm luồng.
L3 giữ thời lượng `given`. `run_demo.py` minh họa riêng nhánh lookup ở P02.
CP-SAT lập lịch, validator kiểm lại, LLM giải thích và L4 cung cấp hai baseline.

Mở `design/wireframes/lead.html` hoặc `nurse.html`. Hai trang nạp lịch đã xuất từ
`demo-data.js`, hiển thị bản nháp và khoảng nghỉ. Các ô hội thoại được khóa trên bản
xem tĩnh. Gửi yêu cầu mới qua `python run.py`, rồi xuất lại để xem lịch mới.

Artifact ghi provider, model và token của lời gọi tóm tắt cuối, cùng phương pháp
lập lịch, validator và metadata dữ liệu tổng hợp. Bản kiểm cục bộ dùng `fake` được
ghi rõ trên giao diện. Đây là kiểm tích hợp trên ca tổng hợp.
Đánh giá sản phẩm dùng benchmark hội thoại theo [hồ sơ eval](../../eval/README.md).

Khoa phát triển demo/UI; các module giữ phân công theo
[contract](../../docs/module-contract.md). Codex hỗ trợ review và kiểm tích hợp.

Snapshot `demo-data.js` đang lưu được Khoa tạo với GPT-4o mini trên nhánh dùng heuristic CP2.
Metadata ghi phương pháp `heuristic_cp2`, dữ liệu tổng hợp và kết quả validator. Lệnh
`build_demo.py` sau tích hợp dùng CP-SAT hiện hành và xuất metadata tương ứng khi chạy lại.
