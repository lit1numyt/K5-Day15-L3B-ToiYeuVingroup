# Pitch deck (HTML, tự chứa)

`index.html` — slide thuyết trình cho sân khấu, đi kèm demo web. Một file, không thư viện,
dùng lại ngôn ngữ thiết kế của web (phẳng, accent sage, hairline).

## Dùng
- **Trình chiếu:** mở `docs/pitch/index.html` trong trình duyệt, bật toàn màn hình (F11).
  `←` / `→` (hoặc click) để chuyển slide; `Home`/`End` về đầu/cuối.
- **Xuất PDF:** `Cmd/Ctrl + P` → hướng ngang (landscape) → Save as PDF (mỗi slide một trang).

## 17 slide (bản technical dive)
1. Bìa · 2. Vấn đề · 3. Nguyên tắc thiết kế · 4. Kiến trúc 4 tầng ·
5. L2 — bài toán xếp lịch CP-SAT (ràng buộc cứng + mục tiêu mềm) ·
6. Gom việc tương thích (clustering) — trước/sau ·
7. Bộ não AI/ML (L1 LLM + L3 hồi quy + L4 KMeans) · 8. Cách huấn luyện & kiểm thử ·
9–10. EDA (phân phối thời lượng, nhu cầu theo giờ) ·
11. L3 — 7 mô hình, baseline thắng · 12. L3 — thực tế vs dự đoán + residual ·
13. L3 — sai số theo loại việc · 14. L3 — đoán thiếu đe doạ giờ nghỉ ·
15. L4 — phân bậc bệnh nhân bằng KMeans · 16. Kết quả · 17. Chuyển sang demo web.

Dùng toàn bộ 9 hình trong [`docs/figures/`](../figures/) (EDA, huấn luyện/kiểm thử L3, cụm L4).
Mọi số là số thật trong repo: benchmark `eval/run-3.csv`, demo `scripts/demo/build_demo.py`,
hình & phân tích L3 theo [`docs/l3-workload-estimator.md`](../l3-workload-estimator.md).
