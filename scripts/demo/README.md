# Demo luồng NurseFlow (chưa có L2)

Một demo chạy được, nối các mảnh đã có thành một luồng lập kế hoạch ca:

```
python scripts/demo/run_demo.py
```

Không cần cài gì thêm (chạy bằng thư viện chuẩn; L4 tự fallback khi thiếu sklearn),
model ở chế độ **fake**.

Luồng demo trên một ca mẫu (`data/preliminary/instances.json`, case P02):
1. **[L3] `estimate_duration`** — điền thời lượng việc còn thiếu từ bảng Simmons (gắn nhãn
   `lookup:simmons…`), giữ nguyên thời lượng đã cho (`given`).
2. **[L4] `classify_patient`** — xếp bệnh nhân thành tier nhẹ/trung bình/nặng (taxonomy KMeans).
3. **[Engine] `answer()`** — agent lập **bản nháp** kế hoạch. L2 CP-SAT chưa có nên dùng
   heuristic thay thế; vẫn qua `validate_plan` (0 vi phạm kỹ năng/coverage).
4. **[L4] `baseline_allocate`** — so với cách truyền thống (theo đầu bệnh nhân và acuity-weighted)
   trên cùng ca: NurseFlow cân bằng tải tốt hơn, ít overhead hơn.

Kết thúc ở trạng thái `draft` (`approval_required=true`) — AI đề xuất, trưởng ca duyệt.

**Giới hạn hiện tại:** L2 là heuristic (chưa phải CP-SAT của Lam); model fake (chưa nối API —
xem `docs/connect-model.md`). Khi hai thứ đó xong, demo không cần đổi: chỉ thay engine/model
phía dưới cùng seam.
