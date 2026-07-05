# Kế hoạch đánh giá demo

## Bộ câu hỏi

Bộ câu hỏi đánh giá nằm tại `data/eval/eval_questions.csv`, gồm 20 câu hỏi về cơ sở dữ liệu:

- Khóa chính
- Khóa ngoại
- SQL JOIN
- Chuẩn hóa cơ sở dữ liệu
- ERD

Mỗi câu có `ground_truth`, `topic` và `question_type` để hỗ trợ chấm thủ công.

## Tiêu chí chấm điểm thủ công

| Tiêu chí | Mô tả | Thang điểm |
| --- | --- | --- |
| Accuracy | Câu trả lời đúng nội dung kỳ vọng không | 1-5 |
| Faithfulness | Câu trả lời có bám sát tài liệu truy xuất không | 1-5 |
| Relevance | Câu trả lời có đúng trọng tâm câu hỏi không | 1-5 |
| Citation | Câu trả lời có nguồn đúng không | Yes/No |
| Hallucination | Câu trả lời có bịa thông tin ngoài tài liệu không | Yes/No |

## Cách chấm

1. Chạy hệ thống với cùng một bộ tài liệu đã index.
2. Hỏi lần lượt các câu trong `data/eval/eval_questions.csv`.
3. So sánh câu trả lời với `ground_truth`.
4. Ghi điểm Accuracy, Faithfulness, Relevance theo thang 1-5.
5. Đánh dấu Citation và Hallucination theo Yes/No.
6. Tính trung bình điểm và tỷ lệ hallucination.

## Bảng so sánh mẫu

| Hệ thống | Accuracy | Faithfulness | Relevance | Hallucination Rate |
| --- | ---: | ---: | ---: | ---: |
| LLM only | 3.2 | 2.8 | 3.5 | 30% |
| RAG | 4.3 | 4.5 | 4.2 | 8% |
| Personalized RAG | 4.4 | 4.5 | 4.3 | 7% |

Các số liệu trên là số liệu minh họa ban đầu cho báo cáo. Khi demo chính thức, có thể thay bằng kết quả chấm thủ công thực tế từ bộ câu hỏi đánh giá.

## Demo flow

1. Tạo user beginner và advanced.
2. Upload tài liệu học tập PDF/DOCX/TXT.
3. Index tài liệu vào ChromaDB.
4. Hỏi chatbot và kiểm tra nguồn tham khảo.
5. Hỏi cùng topic nhiều lần để tạo weak topic.
6. Tạo quiz ôn tập theo topic.
7. Nộp kết quả quiz.
8. Mở dashboard sinh viên để xem tổng số câu hỏi, topic yếu, điểm quiz và gợi ý ôn tập.
