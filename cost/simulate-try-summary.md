# Tóm tắt mô phỏng simulate-try@20261128-142904

Do `python run.py simulate` sinh ra — không sửa tay. Chép bảng sang `cost/cost-estimate.md`.

| Persona | Số phiên mô phỏng | Lượt hỏi / phiên | Token vào / phiên | Token ra / phiên | Gọi model / phiên | Gọi công cụ / phiên |
|---|---:|---:|---:|---:|---:|---:|
| dung_it | 4 | 1 | 1240 | 208 | 1.0 | 0.0 |
| dung_vua | 4 | 3 | 3722 | 421 | 3.0 | 0.0 |
| dung_nhieu | 0 | 5 | — | — | — | — |

Tỉ lệ đạt dùng để tính: 20/20 (100%) — lượt run-3@20261128-115048

- Tỉ lệ đạt lấy từ lượt nhóm chọn: eval/run-3.csv (--rate-from). ⚠️ Lượt này chạy bằng gemini-3.1-flash-lite, mô phỏng đo trên gpt-4o-mini — khác model.

| Model (giá) | Chi phí / phiên | Chi phí / task thành công | Chi phí / câu hỏi đạt | Chi phí / tháng — thấp (300 người) | Chi phí / tháng — cơ sở (700 người) | Chi phí / tháng — cao (1.000 người) | Chi phí / người / tháng (cơ sở) |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite (vào 0.25 · ra 1.5 $/1M) | $0.0011 | $0.0011 | $0.00055 | $3.09 | $7.21 | $10.30 | $0.0103 |
| gemini-4-hydrogen (vào 1.5 · ra 7.5 $/1M) | $0.0061 | $0.0061 | $0.0030 | $17.22 | $40.18 | $57.40 | $0.0574 |

- Chi phí / task thành công = chi phí / phiên ÷ tỉ lệ đạt. Chi phí / câu hỏi đạt = chi phí / phiên ÷ số lượt hỏi trung bình mỗi phiên (2.0) ÷ tỉ lệ đạt — tỉ lệ đạt đo theo từng câu thử.
- Token đo trên model: gpt-4o-mini. Giá tính theo từng model trong bảng — model khác bộ tách token thì số token thật có thể lệch; ghi rõ "đo trên model X, tính giá model Y" trong cost/cost-estimate.md.
- Phiên lỗi (không tính vào trung bình): 0/8.
