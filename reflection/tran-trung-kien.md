# Reflection — Trần Trung Kiên

- **Họ và tên:** Trần Trung Kiên
- **MSSV:** 2A202604014

1. **Vai trò và phần việc**

   - **CP2 & Preliminary CP3:** Khảo sát yêu cầu dữ liệu NurseFlow, so sánh MIMIC-IV-ED Demo với MIMIC-IV Clinical Database Demo (cơ sở cho B16–B18), đề xuất nguồn Zenodo `20754938`, dựng pipeline dịch nhãn – làm sạch – EDA ban đầu tại nhánh `feat/data-pipeline-eda` ([`153d463`](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/commit/153d463) · [Báo cáo EDA](../docs/eda-report.md)).
   - **CP3–CP4 (L1 LLM Orchestrator):** Nối 4 model thật (`anthropic`/`claude`, `openai`, `gemini`, `ollama`) bằng thư viện chuẩn trong [`codebase/ai.py`](../codebase/ai.py), ghép luồng `check_input → L3 estimate_duration → L2 solve_allocation → validate_plan` ([`codebase/tools.py`](../codebase/tools.py) · [`codebase/agent.py`](../codebase/agent.py)), chạy đánh giá lượt 1 đạt 17/20 ([PR #11](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/11) · [`eval/run-1.csv`](../eval/run-1.csv)).
   - **Chốt CP4:** Đối chiếu lỗi lượt 1–2 (`eval/run-2.csv`, 14/20), tinh chỉnh `POLICY` trong `codebase/agent.py`, chạy và chấm lượt 3 đạt **20/20 (100%)**, cập nhật báo cáo đánh giá và `spec.md` ([PR #17](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/17) · [`eval/run-3.csv`](../eval/run-3.csv) · [`eval/report.md`](../eval/report.md)).

2. **AI hỗ trợ thế nào**

   - **Công cụ & phần việc nhờ AI:** Dùng Antigravity / Gemini viết connector REST API (`codebase/ai.py`), ghép L3 vào `codebase/tools.py` và `codebase/agent.py`, sinh unit test (`tests/test_ai.py`, `tests/test_agent.py`), rà bộ quy tắc `POLICY` ([Khai báo AI](../docs/ai-usage.md)).
   - **Phần tự sửa lại từ output AI:**
     - Chặn rò ngữ cảnh giữa các câu hỏi độc lập — tránh lỗi câu B01 kéo sang làm B02 nhận nhầm kỹ năng hô hấp của N3 ([`0119591`](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/commit/0119591)).
     - Tách việc thiếu kỹ năng xác nhận (`vệ sinh`) vào mục chờ trưởng ca duyệt thay vì để model tự gán ([`7d31cab`](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/commit/7d31cab)).
     - Đổi model test từ `gemini-2.5-flash` (404) và `gemini-3.8-flash` (503/timeout) sang `gemini-3.1-flash-lite`, bổ sung mock HTTP test cho 4 provider.

3. **Một câu thử trượt và bài học**

   - **Case `B01` (trượt lượt 1–2):** Có task `vệ sinh` ngoài danh sách kỹ năng điều dưỡng; lượt 1 gán cho N2 (chỉ biết tiêm), lượt 2 gán cho "tất cả điều dưỡng" → vi phạm an toàn cứng ([Lượt 1](../eval/run-1.csv) · [Lượt 2](../eval/run-2.csv)).
   - **Case `B02`, `B04`, `B07` (trượt lượt 1):** Hỏi vặn lại quá kỹ (`need_info`) dù quy tắc chính đã đủ để lên bản nháp có điều kiện ([Báo cáo đánh giá](../eval/report.md)).
   - **Bài học:** Tách bạch rõ trong prompt — việc đủ căn cứ thì ra bản nháp ngay, việc thiếu kỹ năng xác nhận để riêng chờ trưởng ca duyệt; chỉnh prompt xong luôn chạy lại đủ 20 câu tránh hết lỗi hỏi thừa lại dính an toàn cứng ([Lượt 3](../eval/run-3.csv)).
