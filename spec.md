# AI SPEC — NurseFlow (điều phối lại công việc điều dưỡng khi vắng đột xuất) · Nhóm Tôi Yêu Vingroup

> Mốc nộp: §7 chốt chuẩn "đạt" tại **CP2 19:30 Thứ Sáu 27/11** · §0–§7 nộp **CP3 10:00 Thứ Bảy 28/11** · đủ §0–§10 **CP4 14:30 Thứ Bảy 28/11** · §10 changelog ghi tiếp đến **23:59 Thứ Bảy 28/11**.
> Đầu mỗi mục ghi bước guide (`02-guide.md` trong repo đề) chỉ cách điền. Mỗi mục ngắn, có số và nguồn; chi tiết để ở file được trỏ tới. Xoá dòng hướng dẫn trong ngoặc vuông khi điền xong.

Track: [ ] A · [x] B · [ ] C · [ ] D · [ ] E — bài toán: Tối ưu/điều phối công việc điều dưỡng (nurse workforce) — lát cắt: đề xuất phân công lại task khi 1 điều dưỡng vắng đột xuất giữa ca.
Data BTC cấp đã dùng (nếu có — không commit nguyên file): chưa dùng data BTC; dự kiến dùng dữ liệu công khai (MatchRN, McGill workload, Nurse Rostering Benchmarks, KU Leuven) + kịch bản synthetic tự sinh — xem `data/DATA_CARD.md`.

## §0. Hiện tại việc này diễn ra thế nào *(guide 1.1)*
- Luồng hiện tại của việc này, trong khoá hoặc trên app thật (3–5 bước; ảnh chụp từ tài khoản của mình, đã che thông tin):
  1. Đầu ca, điều dưỡng trưởng chia bệnh nhân/điều dưỡng chủ yếu theo số đầu bệnh nhân + kinh nghiệm.
  2. Khi 1 điều dưỡng báo vắng đột xuất (ốm, việc gấp) giữa ca, trưởng ca phải dừng việc để xử lý.
  3. Trưởng ca nhẩm lại: ai đang rảnh, ai đủ kỹ năng cho task đang tồn, task nào sắp đến hạn.
  4. Gọi/nhắn phân công lại thủ công, cập nhật bảng giấy hoặc bảng trắng của khoa.
  (*(tự mô tả theo hiểu biết nhóm; sẽ bổ sung ảnh/trích dẫn phỏng vấn ở CP2)*)
- Công cụ / AI đang được dùng cho việc này (nếu có) + nguồn. Không kiểm được thì ghi "chưa kiểm": chủ yếu thủ công (giấy / bảng trắng / Excel / nhắn tin); AI chuyên dụng cho điều phối lại theo giờ — chưa kiểm.

## §1. Người dùng & bằng chứng *(guide 1.1, 1.2)*
- Người dùng chính (một vai cụ thể): Điều dưỡng trưởng ca của một khoa nội trú cấp tính.
- Việc họ cố làm xong (`động từ + đối tượng + bối cảnh`, không có chữ AI): phân công lại các task điều dưỡng còn tồn/sắp đến hạn khi 1 điều dưỡng vắng đột xuất giữa ca.
- Hôm nay họ giải bằng gì, hỏng ở đâu, vì sao chưa bỏ: tự nhẩm + nhắn tin/bảng trắng; hỏng ở chỗ phải nhớ cùng lúc ai rảnh, ai đủ kỹ năng, task nào đến hạn, có đủ coverage không → chậm và dễ lệch tải; chưa bỏ vì chưa có công cụ nào vừa nhanh vừa tôn trọng ràng buộc an toàn.
- Pain (KHÔNG chữ AI): ai — đang làm gì — vướng đâu — hậu quả gì: Điều dưỡng trưởng ca, đang chia lại việc khi có người vắng, vướng ở việc cân bằng tải + kỹ năng + giờ đến hạn trong đầu, hậu quả là trễ task, lệch tải giữa các điều dưỡng và mất giờ nghỉ thật.
- Bằng chứng — số chính + kết luận (chi tiết: `evidence/summary.md`): *(CP1 — giả thuyết)* khi có người vắng, task bị dồn không đều và tỷ lệ trễ task tăng; số đầu tiên + 1 trích dẫn sẽ bổ sung ở CP2 từ phỏng vấn điều dưỡng và dữ liệu MatchRN/McGill.

## §2. Impact & quyết định chọn *(guide 1.3)*

| Hướng | Bao nhiêu người gặp | Bao nhiêu lần / tháng | Mỗi lần tốn gì | Impact / tháng | Làm kịp không | Chọn? |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

- **Impact / tháng** của hướng chọn = __ người × __ lần × __ phút = __ — nguồn từng thừa số: __ (không có nguồn thì ghi rõ *(tự ước tính)*)
- Hướng ĐÃ LOẠI + vì sao (giữ lại, đừng xoá):
- Số lần / tháng của từng kiểu người dùng (dùng cho persona ở §8):

## §3. Giải pháp tương tự *(guide 2.1)*
- [sản phẩm / tính năng gần giống]: một điều đáng học · một điều đáng né · mình khác gì

## §4. Thiết kế *(guide 2.2, 3.2)*
- **Lát cắt MỘT CÂU** (1 người dùng · 1 việc · 1 quyết định AI · 1 kết quả): Khi 1 điều dưỡng vắng đột xuất, điều dưỡng trưởng ca nhập tình huống khoa → AI đề xuất chuyển các task còn tồn/sắp đến hạn của người vắng sang điều dưỡng còn trống, hợp kỹ năng và không vi phạm coverage → trả **bản nháp phân công lại** để trưởng ca duyệt.
- Không làm (≥3 điều): (1) không tự áp dụng phân công khi chưa có người duyệt; (2) không ra quyết định lâm sàng (chẩn đoán, chỉnh thuốc, tiên lượng bệnh nhân); (3) không lập lịch cả ca từ đầu — chỉ xử lý sự kiện vắng đột xuất; (4) không tích hợp hệ thống bệnh viện thật ở MVP.
- **Sơ đồ** (ảnh / Mermaid / draw.io): [chèn ở đây]
- **Hình dạng:** [ ] workflow cố định · [ ] một agent · [ ] nhiều agent — 2 dòng lý do, và vì sao **không** chọn hình dạng phức tạp hơn:
- **AI dựa vào đâu** — mỗi công cụ (khớp `codebase/tools.py`):

  | Công cụ | Input | Output | Tác động ra ngoài? |
  |---|---|---|---|
  |  |  |  |  |

- **Mức tự động:** [x] AI gợi ý, người quyết · [ ] AI tự làm khi chắc, chuyển người khi không · [ ] AI tự làm — lý do (sai thì ai chịu gì, sửa đắt hay rẻ): phân công sai ảnh hưởng an toàn người bệnh và tải điều dưỡng; sai thì người bệnh/điều dưỡng chịu, sửa rất đắt → AI chỉ tạo bản nháp, trưởng ca duyệt mới áp dụng.
- **Chỗ chặn rủi ro** (rủi ro lớn nhất của lát cắt bị chặn ở đâu, bằng gì):
- **Chỗ người duyệt** (việc AI không được tự làm):
- **Nguyên tắc thiết kế** (≥3, bắt buộc G10):

  | Nguyên tắc | Chỗ cụ thể trên sơ đồ / trong bản chạy thử |
  |---|---|
  | G10 — thu hẹp phạm vi khi không chắc |  |
  |  |  |
  |  |  |

- Phần nào còn giả (công cụ trả dữ liệu giả, model chế độ giả…) — ghi rõ, không giả làm thật:

## §5. Chỗ khó — 4 lớp + ≥6 kịch bản + 2 tấn công *(guide 2.3)*

| Kịch bản | Lớp (1–4) | Hành vi mong muốn (nói gì, hiện gì, cho làm gì tiếp) | Câu thử |
|---|---|---|---|
|  |  |  |  |
| *(tấn công)* |  |  |  |
| *(tấn công)* |  |  |  |

(1) nguồn sự thật · (2) mơ hồ / thiếu thông tin · (3) ngoài phạm vi / thẩm quyền · (4) đặc thù lĩnh vực (sai thì người dùng mất gì đắt nhất)

## §6. Bốn đường đi của trải nghiệm
- Mọi thứ suôn sẻ: · Không chắc (lớp 2): · Không có căn cứ (lớp 1): · Người dùng sửa:
- Bị đòi ngoài phạm vi (lớp 3): · Trường hợp đặc thù lĩnh vực (lớp 4):

## §7. Đánh giá & chuẩn "đạt" *(guide 2.4, 4.1)*
- Data card: `data/DATA_CARD.md` · bộ câu thử: `eval/benchmark.csv` — __ câu (thuong __ · kho __ · tu_choi __) · metric: `eval/metric_spec.yaml` (__ metric)
- **Chuẩn "đạt"** (chốt **trước 19:30 Thứ Sáu 27/11**, giữ nguyên đến 23:59 Thứ Bảy 28/11): "Đạt khi ≥ __% câu qua, và __"
- Kết quả: lượt 1 __/__ (__%) · lượt 2 __/__ (__%) — run ID: __ / __ → chi tiết `eval/report.md`, hồ sơ `eval/README.md`

## §8. Chi phí khi dùng thật *(guide 4.2)*
- Persona + giá: `cost/personas.yaml` · lượt mô phỏng: `cost/simulate-__.csv` (__ phiên)
- Chi phí / task thành công: __ (model __) · __ (model __)
- Chi phí / tháng ở quy mô thật: thấp __ · cơ sở __ · cao __ → chi tiết `cost/cost-estimate.md`
- So với impact / người / tháng (§2): đáng làm không, vì sao:

## §9. Rủi ro & an toàn
- Dữ liệu: đã ẩn danh gì, không thu gì, không đưa gì vào model gói miễn phí:
- AI **không được** làm gì kể cả khi người dùng yêu cầu:
- Ai có thể bị hại nếu AI sai, và nhóm chặn thế nào:

## §10. Phân công & changelog
- Phân công có tên (theo chặng, chia cặp — guide "Cách chia việc"): __
- Dùng AI vào việc gì (2–3 dòng; chi tiết `docs/ai-usage.md`):
- Nhật ký thay đổi — **mọi thay đổi sau CP2 19:30 Thứ Sáu 27/11 phải có dòng ở đây**:

**CP2 → CP4** (vd thu hẹp lát cắt, hỏi thêm người dùng, lần cải tiến trước lượt 2)

| Thời điểm | Đổi gì | Vì sao (trỏ về câu thử / lỗi / bằng chứng nào) |
|---|---|---|
|  |  |  |

**Sau CP4 (đến 23:59 Thứ Bảy 28/11)** (sửa theo góp ý — không sửa chuẩn "đạt", câu thử, số bằng chứng, kết quả các lượt đã chạy)

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
|  |  |  |
