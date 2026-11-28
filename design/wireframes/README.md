# NurseFlow — Wireframes (cổng điều dưỡng)

Hai màn hình mô phỏng **tĩnh** để nhóm thảo luận và để người dựng UI (L1) làm theo.
Không phải sản phẩm chạy được — chỉ bố cục + kiểu.

## Mở thế nào
Mở trực tiếp trong trình duyệt (không cần server):

```
design/wireframes/index.html   → trang đích, dẫn vào hai màn hình
design/wireframes/nurse.html   → màn hình điều dưỡng
design/wireframes/lead.html    → màn hình trưởng ca
```

## Các màn hình
- **Điều dưỡng (`nurse.html`)** — xem ca cá nhân:
  - *Dải tổng quan* ngang trên cùng (đã xong / còn lại / việc kế / thời gian còn lại / giờ nghỉ).
  - *Nửa trái:* lịch ca dạng lịch (3 ca chuẩn, mock hiển thị ca sáng 07:00–15:00). Khối việc đặt theo giờ;
    **việc làm song song nằm cạnh nhau** (hai làn). Dưới là *thứ tự thao tác* xen kẽ `1.1 → 2.1 → 1.2 → 2.2`.
  - *Nửa phải:* chat đơn giản — hỏi AI về cách sắp xếp, hoặc **đề xuất thay đổi** (gửi trưởng ca duyệt).
    Điều dưỡng **không** tự áp dụng thay đổi.
- **Trưởng ca (`lead.html`)** — đơn giản hơn:
  - *Dải tổng quan* (điều dưỡng trực / tổng việc / % hoàn thành / yêu cầu chờ duyệt / coverage).
  - *Nửa trái:* lịch cả ca cho **toàn bộ điều dưỡng** (mỗi hàng một người, dạng gantt).
  - *Nửa phải:* chat — **duyệt/từ chối** đề xuất của điều dưỡng, và **gửi yêu cầu tới hệ thống**.

## Khớp với sản phẩm
Phản ánh lát cắt ở [`spec.md`](../../spec.md) §4 và [`docs/module-contract.md`](../../docs/module-contract.md):
AI **đề xuất bản nháp**, trưởng ca **duyệt**, điều dưỡng **không tự áp dụng**. Lời giải thích của AI trong
chat nêu căn cứ cụ thể (khớp metric `giai_thich_co_can_cu`).

## Kiểu & ràng buộc
- Dùng design kit ở [`style/`](../../style/STYLE.md): phẳng, hairline 1px, một accent sage, **không đổ bóng /
  gradient / nút tô màu**, chữ weight 400/500/600. Màu/kiểu lấy từ `style/style.css` (tokens); phần dashboard
  thêm ở `wireframe.css` — không hard-code màu ngoài tokens.
- **Khoá chế độ sáng**: kit vốn theo OS (sáng/tối); `wireframe.css` ghi đè token tối về sáng nên mock luôn sáng.
- **Tĩnh, không JavaScript.** Vị trí khối việc/gantt là số cố định (mock). Khi dựng UI thật, tính vị trí từ
  giờ bắt đầu/thời lượng; dữ liệu kế hoạch lấy từ output của agent (schema `plan` trong module-contract §2.2).

## Bàn giao cho L1
Tái dùng `../../style/style.css` + `wireframe.css`. Các component đã đặt tên class: `.ov` (dải tổng quan),
`.board` (chia 2 cột), `.cal`/`.ev` (lịch điều dưỡng + khối việc), `.flow` (thứ tự thao tác), `.chat`/`.msg`
(chat), `.gantt`/`.bar` (lịch cả ca), `.req` (thẻ yêu cầu chờ duyệt).
