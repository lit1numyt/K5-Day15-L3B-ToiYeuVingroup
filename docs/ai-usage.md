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

## CP3 · Tích hợp L1 LLM Orchestrator

| Phần CP3 | Công cụ hỗ trợ | Công việc và cách kiểm | Phụ trách |
|---|---|---|---|
| Nối API model & luồng L1 | Antigravity / Gemini | Hỗ trợ viết nhánh gọi API (`anthropic`/`openai`/`gemini`/`ollama`) trong `codebase/ai.py`, tích hợp L3 `estimate_duration` vào `codebase/tools.py` & `codebase/agent.py`, thêm bộ điều phối hội thoại và hậu kiểm an toàn. Đã kiểm bằng 146 unit test (`tests/`), 15 fixture CP2, `run.py check` và lượt eval thật `eval/run-1.csv` (17/20 = 85%). | Kiên |
