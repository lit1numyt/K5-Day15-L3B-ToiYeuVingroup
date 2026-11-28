# NurseFlow — Wireframes (cổng điều dưỡng)

Hai màn hình hiển thị lịch đầu ca từ file do pipeline xuất, phục vụ demo và thảo luận UI.
Lệnh xuất và phạm vi tương tác được ghi trong [hướng dẫn demo](../../scripts/demo/README.md).

## Mở thế nào
Mở trực tiếp trong trình duyệt (không cần server). Vào bằng trang đăng nhập:

```
design/wireframes/login.html   → ĐĂNG NHẬP (điểm vào; index.html tự chuyển về đây)
design/wireframes/nurse.html   → màn hình điều dưỡng (tự chuyển về login nếu chưa đăng nhập)
design/wireframes/lead.html    → màn hình trưởng ca (chỉ vai trò trưởng ca)
```

## Đăng nhập (mock phía client)
Tài khoản IT cấp (không có đăng ký). **Đăng nhập mô phỏng cho demo — không phải bảo mật thật**
(mật khẩu nằm trong `accounts.js`). Mật khẩu chung: `vinai_hackathon`.

| Họ tên | Tài khoản | Vai trò | Thấy gì |
|---|---|---|---|
| Nguyễn Thị An | `annt` | Điều dưỡng (N1) | ca của riêng An |
| Trần Văn Bình | `binhtv` | Điều dưỡng (N2) | ca của riêng Bình |
| Lê Thị Cúc | `cuclt` | Điều dưỡng (N3) | ca của riêng Cúc |
| Phạm Minh Dũng | `dungpm` | Điều dưỡng (N4) | ca của riêng Dũng |
| Hoàng Thị Hoa | `hoaht` | Điều dưỡng (N5) | ca của riêng Hoa |
| Đông Hữu Nguyễn Khoa | `khoadhn` | Trưởng ca | lịch cả 5 điều dưỡng |

Phiên lưu ở `sessionStorage`; có dự phòng `?u=<tài khoản>` để chạy tốt trên `file://`.
"Đăng xuất" xoá phiên và quay về `login.html`. Tài khoản và dữ liệu do
`scripts/demo/build_demo.py` sinh ra (`accounts.js` + `demo-data.js`).

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
- `render.js` đọc `demo-data.js`, tính vị trí từ giờ bắt đầu/thời lượng và hiển thị
  bản nháp từ output của agent. Hội thoại và yêu cầu mới thực hiện qua CLI rồi xuất lại lịch.

## Bàn giao cho L1
Tái dùng `../../style/style.css` + `wireframe.css`. Các component đã đặt tên class: `.ov` (dải tổng quan),
`.board` (chia 2 cột), `.htl` + `.bar` (timeline ngang — dùng chung cho cả hai màn hình: nurse có 2 làn,
lead có một hàng mỗi điều dưỡng), `.flow` (thứ tự thao tác), `.chat`/`.msg` (chat), `.req` (thẻ yêu cầu chờ
duyệt). Trang điều dưỡng khoá gọn một màn hình bằng `body.app` (chỉ ở desktop ≥64rem).

Trong `.htl`, mỗi khối việc đặt bằng `left`/`width` theo **phần trăm của cả ca** (vd ca 8 giờ → 1 giờ = 12.5%),
nên không có phép tính pixel dễ lệch. Khi dựng thật: `left = (bắt đầu − đầu ca)/độ dài ca`, `width = thời lượng/độ dài ca`.
