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
- **Điều dưỡng (`nurse.html`)** — xem ca cá nhân, **gói gọn trong một màn hình** (khoá viewport ở ≥64rem,
  dưới mức đó cuộn bình thường):
  - *Dải tổng quan* ngang trên cùng (đã xong / còn lại / việc kế / thời gian còn lại / giờ nghỉ).
  - *Timeline ngang* (toàn chiều rộng): trục giờ theo ca (3 ca chuẩn; mock là ca sáng 07:00–15:00), khối việc
    đặt theo giờ trên **hai làn** — việc làm song song nằm ở hai làn khác nhau.
  - *Bên dưới, hai cột:* trái là *thứ tự thao tác* xen kẽ `1.1 → 2.1 → 1.2 → 2.2`; phải là chat đơn giản —
    hỏi AI, hoặc **đề xuất thay đổi** (gửi trưởng ca duyệt). Điều dưỡng **không** tự áp dụng thay đổi.
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
`.board` (chia 2 cột), `.htl` + `.bar` (timeline ngang — dùng chung cho cả hai màn hình: nurse có 2 làn,
lead có một hàng mỗi điều dưỡng), `.flow` (thứ tự thao tác), `.chat`/`.msg` (chat), `.req` (thẻ yêu cầu chờ
duyệt). Trang điều dưỡng khoá gọn một màn hình bằng `body.app` (chỉ ở desktop ≥64rem).

Trong `.htl`, mỗi khối việc đặt bằng `left`/`width` theo **phần trăm của cả ca** (vd ca 8 giờ → 1 giờ = 12.5%),
nên không có phép tính pixel dễ lệch. Khi dựng thật: `left = (bắt đầu − đầu ca)/độ dài ca`, `width = thời lượng/độ dài ca`.
