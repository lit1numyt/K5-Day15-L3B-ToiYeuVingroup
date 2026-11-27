# Contribution Guide — Nhóm Tôi Yêu Vingroup (NurseFlow)

> Quy ước commit & branch cho cả nhóm. Mục tiêu: `main` luôn chạy được, lịch sử dễ đọc, không ai đạp lên việc của nhau.
> Luật cấm (không commit secret, không sửa file khung…) nằm ở [`AGENTS.md`](AGENTS.md) — đọc trước khi code.

## 1. Mô hình nhánh

Ba tầng, không bao giờ commit thẳng lên `main`:

| Nhánh | Dùng để | Ai đẩy |
|---|---|---|
| `main` | Bản **ổn định**, dùng để nộp checkpoint. Chỉ nhận merge từ `develop`. | Chỉ đội trưởng, sau khi `develop` đã xanh |
| `develop` | Nhánh **tích hợp**: gộp mọi feature đã xong. Phải `python run.py check` sạch trước khi merge lên `main`. | Qua PR / merge từ nhánh feature |
| `feat/*`, `fix/*`, `docs/*`, `chore/*` | Nhánh làm việc, mỗi người/mỗi việc một nhánh, tách **từ `develop`**. | Người phụ trách |

Luồng chuẩn:

```
develop ──┬─> feat/xep-lich ──(PR)─> develop ──(ổn định)─> main
          └─> feat/dashboard ─(PR)─> develop
```

## 2. Đặt tên nhánh

`<loại>/<mô-tả-ngắn-không-dấu>` — ví dụ:

- `feat/shift-orchestrator` — thêm tính năng
- `fix/coverage-constraint` — sửa lỗi
- `docs/spec-section-5` — tài liệu
- `chore/requirements` — lặt vặt (config, deps, dọn dẹp)

Loại: `feat` · `fix` · `docs` · `chore` · `test` · `refactor`.

## 3. Commit atomic

**Một commit = một thay đổi logic hoàn chỉnh.** Đừng gộp "sửa lỗi + đổi tên biến + thêm tính năng" vào một commit.

- Commit chạy được, không để nửa vời (code lỗi cú pháp, test đỏ).
- Thay đổi không liên quan → tách commit khác.
- Commit nhỏ, thường xuyên; dễ review và dễ revert khi cần.

### Định dạng message

```
<loại>(<phạm vi>): <tóm tắt, tiếng Việt, ≤ 72 ký tự, động từ ở đầu>

<thân (tùy chọn): vì sao đổi, tham chiếu CP/câu thử/lỗi nào>
```

Ví dụ:

```
feat(agent): thêm bước gom việc tương thích trước khi gán điều dưỡng

Giảm việc phân mảnh theo Problem-Gap-Solution §3.2. Chưa nối model
thật — vẫn chế độ giả cho tới CP3.
```

## 4. Trước khi mở PR / merge

- [ ] `python run.py check` không báo lỗi format (cảnh báo CP sau thì được).
- [ ] `python run.py` chạy hết luồng (chế độ giả cũng phải xong).
- [ ] Không commit `.env`, API key, data gốc BTC cấp, dữ liệu bệnh nhân thật (xem `AGENTS.md`).
- [ ] Không sửa file khung (`codebase/tracing.py`, `eval/run_eval.py`, `cost/simulate.py`, `run.py`) và các file đã chạy (`eval/run-*.csv`, `cost/simulate-*.csv`, `traces/*`).
- [ ] Rebase/merge `develop` mới nhất vào nhánh để tránh xung đột.

## 5. Merge

- Merge vào `develop` và `main` dùng **`--no-ff`** để giữ dấu vết nhánh:
  ```
  git checkout develop && git merge --no-ff feat/ten-nhanh
  ```
- **Đội trưởng (Khoa)** là người duyệt cuối trước khi `develop` → `main`.
- Sau CP2 19:30: mọi thay đổi phải có dòng trong changelog `spec.md` §10.

## 6. Khi kẹt

- Xung đột merge không chắc → hỏi trong nhóm, đừng `--force` lên `develop`/`main`.
- Lỡ commit nhầm file nhạy cảm → báo đội trưởng ngay, đừng chỉ `rm` ở commit sau.
