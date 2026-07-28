# Báo cáo thực tập tuần 8 - Nhật ký 1

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Phân tích yêu cầu tuần 8 về quiz, recommendation, dashboard và đánh giá hệ thống.
- Chuyển model `QuizResult` từ placeholder sang SQLAlchemy model thật tại `backend/models/quiz_result.py`.
- Import `QuizResult` vào `backend/main.py` để tạo bảng `quiz_results`.
- Xây dựng service sinh quiz tại `backend/services/quiz_generator.py`.
- Thiết kế prompt sinh câu hỏi trắc nghiệm từ context RAG.
- Yêu cầu LLM trả về JSON gồm câu hỏi, 4 lựa chọn A/B/C/D, đáp án đúng và giải thích.
- Bổ sung hàm `_extract_json()` để parse response JSON từ LLM.
- Xử lý trường hợp LLM trả JSON trong markdown code block.
- Xây dựng router quiz tại `backend/routers/quiz.py`.
- Thêm endpoint `POST /quiz/generate`.
- Thêm endpoint `POST /quiz/submit`.
- Thêm endpoint `GET /quiz/results/{user_id}`.
- Kiểm thử API `POST /quiz/submit` và `GET /quiz/results/{user_id}` không phụ thuộc Gemini.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách thiết kế prompt yêu cầu LLM trả về JSON có cấu trúc.
- Biết cách parse response LLM khi có thể phát sinh markdown code block hoặc nội dung ngoài JSON.
- Áp dụng FastAPI và Pydantic để validate request tạo quiz và nộp quiz.
- Áp dụng SQLAlchemy để lưu điểm quiz theo user, course và topic.
- Hiểu cách tách chức năng generate quiz và submit result thành hai API riêng.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **8/10**

Lý do:

- Đã hoàn thành model quiz result, quiz generator và Quiz API.
- API lưu kết quả quiz đã test thành công.
- Chưa chấm cao hơn vì phần sinh quiz thật vẫn phụ thuộc quota/API key Gemini.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    [8]    9    10
```

### Khó khăn/vướng mắc gặp phải

- LLM có thể không trả JSON chuẩn dù prompt đã yêu cầu.
- Nếu Gemini hết quota, endpoint generate quiz không thể sinh câu hỏi thật.
- Cần tránh lỗi chia cho 0 khi lưu điểm quiz.
- Cần validate số câu đúng không lớn hơn tổng số câu.

### Cách xử lý hoặc hướng giải quyết

- Viết parser để cố gắng trích JSON từ response.
- Nếu parse thất bại, API trả `raw_response` và thông báo lỗi rõ ràng.
- Dùng `Field(ge=1)` cho `total_questions`.
- Kiểm tra `correct_answers <= total_questions` trước khi lưu kết quả.
- Test phần submit quiz độc lập với LLM.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong giai đoạn này.

### Bạn cần GVHD hỗ trợ gì không

- Góp ý định dạng quiz có phù hợp để demo không.
- Hỗ trợ xác nhận số lượng câu hỏi quiz mặc định nên là 5 hay cần ít hơn để demo nhanh.
- Góp ý cách trình bày hạn chế khi LLM trả JSON không chuẩn.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Chức năng quiz giúp hệ thống không chỉ dừng ở hỏi đáp mà còn hỗ trợ ôn tập chủ động. Đây là phần có giá trị khi trình bày sản phẩm vì sinh viên có thể đọc tài liệu, hỏi chatbot, sau đó làm quiz để tự kiểm tra mức độ hiểu bài.

### Kế hoạch làm việc tiếp theo

- Xây dựng recommendation dựa trên weak topics.
- Xây dựng dashboard học tập.
- Bổ sung quiz và dashboard vào Streamlit UI.
- Tạo bộ câu hỏi đánh giá và tiêu chí chấm điểm.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 8_NhatKy1_Quiz_API_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh code `quiz_result.py`.
- Ảnh code `quiz_generator.py`.
- Ảnh Swagger endpoint `POST /quiz/generate`.
- Ảnh Swagger endpoint `POST /quiz/submit`.
- Ảnh kết quả lưu quiz result trong database.

