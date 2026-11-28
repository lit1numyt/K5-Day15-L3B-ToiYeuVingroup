# Khai báo dùng AI

| Phần CP2 | Công cụ hỗ trợ | Công việc và cách kiểm | Phụ trách |
|---|---|---|---|
| Dữ liệu | Codex | Hỗ trợ đọc codebook, viết script EDA và đối chiếu số liệu với các bảng MatchRN, MIMIC-IV Demo. | Lam |
| Lập kế hoạch và đánh giá | Codex | Hỗ trợ viết fixture, mã lập lịch, validator, câu hỏi từ dữ liệu và trình bày kết quả. Đầu ra được kiểm lại theo ràng buộc, có test cho lịch sai. | Lam |

Số liệu khảo sát và sự kiện lấy từ nguồn công khai ghi trong [data card](../data/DATA_CARD.md). Hồ sơ [đánh giá](../eval/README.md) ghi rõ phương pháp tự soát và kết quả đã đo.

## Preliminary CP3

Lam và Kiên chủ trì nghiên cứu, lựa chọn dữ liệu và phương pháp. Kiên đề xuất nguồn và
thực hiện pipeline, bản dịch, EDA ban đầu tại commit `153d463`. Lam phụ trách kiểm chứng,
hoàn thiện xử lý dữ liệu, feature engineering và quyết định phương án bàn giao theo kiến trúc nhóm.

Codex hỗ trợ tham vấn, lập trình, đối chiếu tài liệu nguồn, chạy kiểm tra và biên tập báo cáo.
Kết quả được lưu cùng mã tái lập và tham chiếu nguồn trong hồ sơ Preliminary. Nhóm chịu
trách nhiệm về lựa chọn phương pháp, nội dung báo cáo và việc tích hợp vào project.
[Báo cáo Preliminary](eda-report.md) · [Data card](../data/DATA_CARD.md).

## L2 CP3

Lam phụ trách mô hình CP-SAT, validator, thiết kế ca kiểm và đối chứng theo kiến trúc nhóm.
Codex hỗ trợ lập trình, kiểm ràng buộc, chạy phép đo và biên tập hồ sơ. L4 được kế thừa từ
nhánh Khoa, giữ tác giả và mô hình gốc; phần hỗ trợ chỉ điều chỉnh trạng thái continuity và
cách chấm lại phép so. L3 của Tiệp được kiểm ở giao diện tích hợp, không nhận là phần Lam viết.

## CP3 · Tích hợp L1 LLM Orchestrator

| Phần CP3 | Công cụ hỗ trợ | Công việc và cách kiểm | Phụ trách |
|---|---|---|---|
| Nối API model & luồng L1 | Antigravity / Gemini | Hỗ trợ viết nhánh gọi API (`anthropic`/`openai`/`gemini`/`ollama`) trong `codebase/ai.py`, tích hợp L3 `estimate_duration` vào `codebase/tools.py` & `codebase/agent.py`, thêm bộ điều phối hội thoại và hậu kiểm an toàn. Đã kiểm bằng 146 unit test (`tests/`), 15 fixture CP2, `run.py check` và lượt eval thật `eval/run-1.csv` (17/20 = 85%). | Kiên |
| Cải tiến POLICY L1 (CP4) | Antigravity / Gemini | Tinh chỉnh bộ quy tắc `POLICY` tổng quát trong `codebase/agent.py` để khắc phục lỗi `B01`, `B02`, `B07`, `B08`, `B09`, `B14`, `B15`; kiểm lại unit test L1/AI và chạy/chấm `eval/run-3.csv` đạt 20/20 (100%). | Kiên |

Khoa thiết kế và triển khai demo xuất lịch ra wireframe, policy hội thoại trực tiếp và lượt
đánh giá GPT-4o mini trên nhánh demo. Lam hỗ trợ tích hợp với L3, L2 CP-SAT và validator hiện hành,
đối chiếu số liệu và nội dung giao diện. Codex hỗ trợ review, sửa lỗi tích hợp và chạy kiểm tra.
Phạm vi đo và lưu ý chấm nhãn được trình bày trong [báo cáo đánh giá](../eval/report.md).
