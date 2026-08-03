# Kế hoạch và kết quả đánh giá

## Bộ câu hỏi

Bộ câu hỏi đánh giá nằm tại `data/eval/eval_questions.csv`, gồm 50 câu hỏi về cơ sở dữ liệu (20 câu biên soạn tay + 30 câu tự sinh bám theo ranh giới chunk thật):

- Khóa chính, khóa ngoại
- SQL JOIN
- Chuẩn hóa cơ sở dữ liệu
- ERD

Mỗi câu có `topic` và `question_id`. Gold chunk tương ứng (chunk nào được coi là "đúng" cho từng câu hỏi) nằm tại `data/eval/gold_chunks.csv`.

## Đánh giá Retrieval (đo tự động, số liệu thật)

Đo bằng `scripts/evaluate_retrieval.py` trên 6 cấu hình pipeline:

| Cấu hình | Mô tả |
| --- | --- |
| A | Dense only (vector search) |
| B | Hybrid (Dense + BM25 + RRF) |
| C | Hybrid + Reranker — **cấu hình mặc định của hệ thống** |
| D | Hybrid + Reranker + Multi-Query (luôn bật) |
| E | Hybrid + Reranker + Query Decomposition (luôn bật) |
| F | Hybrid + Reranker + On-demand routing (Query Decomposition + Multi-Query tự động, chỉ bật khi cần) |

Chỉ số đo: HitRate@1/3/5/10, Recall@10, MRR@10, Precision@3, nDCG@10, latency (mean/median/p95), kèm khoảng tin cậy 95% (bootstrap) cho HitRate.

**Kết quả cấu hình C** (Hybrid + Reranker, n=40 câu có gold): HitRate@1 = 72.5%, HitRate@3 = 87.5%, HitRate@5 = 87.5%, HitRate@10 = 95.0%, MRR@10 = 0.807, nDCG@10 = 0.828, latency trung bình ≈ 665 ms (median 662 ms, p95 819 ms).

**Cấu hình D** (Multi-Query luôn bật) cho HitRate/MRR thấp hơn C (MRR@10 = 0.721) trong khi latency trung bình tăng lên ≈ 7143 ms (median 7205 ms) — hơn 10 lần so với C. Đây là lý do Multi-Query không bật mặc định mà chỉ bật on-demand (cấu hình F) khi kết quả lượt truy xuất đầu có độ tin cậy thấp.

Bảng chi tiết đầy đủ theo từng cấu hình: `reports/eval/retrieval_eval_table.md`, `reports/eval/retrieval_eval_summary.csv`, `reports/eval/retrieval_eval_per_query.csv`.

Ngoài ra còn hai thực nghiệm quét tham số chunking (không đổi thứ hạng cấu hình, chỉ tối ưu chất lượng chunk semantic): quét ngưỡng percentile breakpoint (`reports/eval/percentile_sweep_table.md`) và quét số câu overlap giữa các chunk (`reports/eval/overlap_sweep_table.md`).

## Đánh giá Generation (đo tự động, số liệu thật)

Đo bằng `scripts/evaluate_generation.py`, theo phương pháp claim-level (kiểu RAGAS): tách câu trả lời thành các claim, kiểm tra từng claim có được ngữ cảnh truy xuất hỗ trợ không (Faithfulness), và câu trả lời có bám sát câu hỏi không (Answer Relevancy).

**Kết quả** (cấu hình C, n=50 câu hỏi): 7/50 câu (14%) trả lời "không đủ thông tin"; trong số 43 câu có câu trả lời, Faithfulness trung bình = 0.982, Answer Relevancy trung bình = 0.693.

Chi tiết từng câu: `reports/eval/generation_eval_per_query.csv`, `reports/eval/generation_eval_table.md`, `reports/eval/generation_eval_summary.json`.

## Đánh giá thủ công (tùy chọn, bổ sung cho demo)

Ngoài số liệu tự động trên, có thể chấm thủ công nhanh khi demo trực tiếp theo các tiêu chí sau (thang 1-5, riêng Citation/Hallucination là Yes/No):

| Tiêu chí | Mô tả |
| --- | --- |
| Accuracy | Câu trả lời đúng nội dung kỳ vọng không |
| Faithfulness | Câu trả lời có bám sát tài liệu truy xuất không |
| Relevance | Câu trả lời có đúng trọng tâm câu hỏi không |
| Citation | Câu trả lời có nguồn đúng không |
| Hallucination | Câu trả lời có bịa thông tin ngoài tài liệu không |

Cách chấm: chạy hệ thống với cùng bộ tài liệu đã index, hỏi lần lượt các câu trong `data/eval/eval_questions.csv`, ghi điểm theo bảng trên. Đây là bước kiểm tra bổ sung mang tính định tính — số liệu chính thức, có thể tái lập, dùng cho báo cáo là kết quả tự động ở hai mục phía trên.

## Bộ test tự động (pytest)

`python -m pytest tests/` — 70/70 test pass, phủ các router auth/users/courses/documents/chat/quiz/dashboard và topic taxonomy.

## Demo flow

1. Đăng nhập bằng tài khoản demo (`admin@edu.ai` / `Admin@123` hoặc `student@edu.ai` / `Student@123`, tạo bằng `scripts/seed_auth.py`).
2. Tạo user beginner và advanced nếu cần so sánh cá nhân hóa theo trình độ.
3. Upload tài liệu học tập PDF/DOCX/TXT.
4. Index tài liệu vào ChromaDB (tự động trong lúc upload).
5. Hỏi chatbot và kiểm tra nguồn tham khảo.
6. Hỏi cùng topic nhiều lần để tạo weak topic.
7. Tạo quiz ôn tập theo topic.
8. Nộp kết quả quiz.
9. Mở dashboard sinh viên để xem tổng số câu hỏi, topic yếu, điểm quiz và gợi ý ôn tập.
