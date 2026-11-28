# Reflection — Nguyễn Quang Tiệp

1. **Vai trò và phần việc**

   Ở CP1–CP2, tôi làm khảo sát tài liệu về bối cảnh phân công điều dưỡng (gồm Medtasker và NurseXT) và nghiên cứu workload, thời gian nghỉ. Từ đó tôi đề xuất ngưỡng 30 phút nghỉ liên tục, trần 450 phút cho ca 8 giờ và phương án nghỉ PA3. [Khảo sát](../NurseFlow_Survey.md) · [Nghiên cứu workload](../evidence/workload-research.md) · [PR #1](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/1) · [PR #3](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/3)\
   Ở CP3, tôi phụ trách L3 `estimate_duration` theo contract §3.3 của Khoa. Task đã có phút thì giữ nguyên, thiếu phút thì tra bảng Simmons Table 3 khi đủ điều kiện, còn lại trả `need_info`. L3 không tự đặt con số nào. [Mã L3](../codebase/workload/estimator.py) · [Báo cáo L3](../docs/l3-workload-estimator.md) · [PR #7](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/7)\
   Tôi chạy thực nghiệm ML/DL trên 2.192 episode phòng mổ Zenodo (median, Ridge, RF, GBT, MLP, GroupKFold theo nhân viên). Tôi chọn Ridge cho nhánh thực nghiệm vì bias gần 0 và tỷ lệ dự đoán thiếu 35%, so với 47% của median. Model này không đưa vào production. [Script](../scripts/l3/train_or_experiment.py) · [Artifact](../artifacts/l3/or_experiment_summary.json)\
   Sau review, tôi sửa lỗi ở PR #9 và thêm 30 test hồi quy. Bộ test L3 đạt 78 OK, P01–P03 khớp bộ bàn giao của Lam. [Test hồi quy](../tests/test_workload_regression.py) · [PR #9](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/9)

2. **AI hỗ trợ tôi thế nào**

   Tôi dùng Claude Code (Claude Opus) để tìm và tóm tắt tài liệu, viết mã L3 và script thực nghiệm, sinh test, vẽ biểu đồ và biên tập báo cáo. Các commit có AI hỗ trợ đều ghi `Co-Authored-By`. Tôi tự quyết định nguồn dữ liệu, tiêu chí chọn model và ranh giới production/thực nghiệm.\
   Review PR #7 phát hiện hai lỗi P1 trong mã AI viết. Task có `duration_source: null` làm `assert` văng lỗi. Task cần hai nhân viên mà đã có phút thì lọt thẳng xuống solver, trong khi L2 chỉ giao một người cho mỗi task. Tôi bỏ `assert` runtime, chặn các task này thành `need_info`, kiểm kiểu input và bắt lỗi bảng nguồn (NaN, Infinity, DOI sai). [PR #9](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/9)\
   AI cũng tự thêm dòng changelog vào `spec.md`, vượt phạm vi PR, nên tôi gỡ ở [PR #5](https://github.com/lit1numyt/K5-Day15-L3B-ToiYeuVingroup/pull/5). Trong thực nghiệm, tôi giữ cả 261 outlier thay vì xóa để MAE đẹp hơn. Tôi cũng ghi rõ giới hạn nested CV của Ridge và kết quả holdout theo thời gian còn thiếu 12,67 phút mỗi episode. [Báo cáo L3 §7](../docs/l3-workload-estimator.md)

3. **Một câu thử trượt của nhóm và bài học**

   Ở câu B15 của lượt 2, đề bài cho ca 8 giờ, 28 bệnh nhân, 6 RN và yêu cầu tính số phút công việc của mỗi RN. Model lấy 480 phút chia cho 6 ra 80 phút mỗi người, và câu được chấm `pass=0`. [Kết quả lượt 2](../eval/run-2.csv)\
   Đây đúng là điều L3 được thiết kế để chặn: không có danh sách task, thời lượng có nguồn và capacity từng người thì phải hỏi lại. Nhưng câu này không đi qua L3, vì L1 trả lời trực tiếp bằng model ngôn ngữ. Ở lượt 3, Kiên bổ sung POLICY tổng quát cho L1 và câu này đạt. [Kết quả lượt 3](../eval/run-3.csv) · [Bộ câu thử](../eval/benchmark.csv)\
   Bài học tôi rút ra là một nguyên tắc an toàn chỉ có tác dụng khi mọi đường trả lời đều phải tuân theo. Viết đúng trong một module là chưa đủ. Lần sau, tôi sẽ viết benchmark cho mỗi quy tắc của module mình ở mức toàn hệ thống, như tôi đã đề xuất B16/B17/B19/B20 phải hỏi lại thay vì đoán, và phối hợp với người làm L1 để quy tắc đó có trong cả POLICY.
