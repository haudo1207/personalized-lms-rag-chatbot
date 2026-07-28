# Báo cáo thực tập tuần 8

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Xây dựng model `QuizResult` bằng SQLAlchemy để lưu kết quả làm quiz.
- Import `QuizResult` vào `backend/main.py` để tạo bảng `quiz_results`.
- Xây dựng service sinh quiz tại `backend/services/quiz_generator.py`.
- Thiết kế prompt tạo câu hỏi trắc nghiệm dựa trên tài liệu truy xuất từ RAG.
- Bổ sung xử lý parse JSON khi LLM trả về quiz, kể cả trường hợp JSON nằm trong code block.
- Xây dựng Quiz API tại `backend/routers/quiz.py`.
- Thêm endpoint `POST /quiz/generate` để sinh quiz từ tài liệu.
- Thêm endpoint `POST /quiz/submit` để lưu kết quả quiz.
- Thêm endpoint `GET /quiz/results/{user_id}` để xem kết quả quiz.
- Xây dựng service gợi ý ôn tập tại `backend/services/recommendation.py`.
- Xây dựng dashboard service tại `backend/services/dashboard_service.py`.
- Thay router dashboard bằng endpoint `GET /dashboard/student/{user_id}?course_id=...`.
- Dashboard trả về tổng số câu hỏi, topic yếu, kết quả quiz, điểm trung bình và gợi ý ôn tập.
- Cập nhật Streamlit UI, bổ sung khu vực tạo quiz, nộp kết quả quiz và xem dashboard học tập.
- Viết lại `README.md` sạch UTF-8, đầy đủ chức năng, cách cài đặt, cách chạy và demo flow.
- Tạo bộ câu hỏi đánh giá tại `data/eval/eval_questions.csv` gồm 20 câu hỏi.
- Tạo tài liệu kế hoạch đánh giá tại `docs/evaluation_plan.md`.
- Bổ sung bảng tiêu chí đánh giá thủ công và bảng so sánh mẫu giữa LLM only, RAG và Personalized RAG.
- Kiểm thử compile backend/app và test API quiz submit, quiz results, dashboard.
- Commit và push mã nguồn tuần 8 lên GitHub.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách tạo quiz trắc nghiệm từ context RAG bằng LLM.
- Biết cách thiết kế prompt yêu cầu LLM trả về JSON có cấu trúc.
- Biết cách xử lý lỗi khi response của LLM không phải JSON hợp lệ.
- Áp dụng FastAPI để xây dựng API generate quiz, submit quiz và lấy kết quả quiz.
- Áp dụng SQLAlchemy để lưu điểm quiz và truy vấn kết quả theo user/course.
- Biết cách xây dựng dashboard học tập đơn giản từ dữ liệu chat history, weak topics và quiz results.
- Biết cách tạo gợi ý ôn tập dựa trên topic yếu của sinh viên.
- Biết cách xây dựng bộ câu hỏi đánh giá và tiêu chí chấm thủ công cho hệ thống RAG.
- Hiểu cách trình bày so sánh LLM thường, RAG và Personalized RAG trong báo cáo.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **9/10**

Lý do:

- Đã hoàn thành các chức năng cuối: quiz, lưu kết quả, recommendation, dashboard, bộ câu hỏi đánh giá và README.
- Các endpoint không phụ thuộc LLM như submit quiz, xem kết quả và dashboard đã test thành công.
- UI đã có đủ luồng demo cuối.
- Chưa chấm 10/10 vì chức năng sinh quiz thật vẫn phụ thuộc quota/API key Gemini.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    8    [9]    10
```

### Khó khăn/vướng mắc gặp phải

- Quiz generator phụ thuộc LLM nên vẫn có rủi ro lỗi nếu Gemini hết quota.
- LLM có thể trả JSON không chuẩn, ví dụ kèm thêm giải thích hoặc bọc trong markdown code block.
- Cần thiết kế UI quiz sao cho vừa hiển thị câu hỏi, vừa cho phép chọn đáp án và submit điểm.
- Dashboard cần tổng hợp dữ liệu từ nhiều bảng: `chat_history`, `weak_topics`, `quiz_results`.
- README cũ có lỗi hiển thị tiếng Việt nên cần viết lại sạch.

### Cách xử lý hoặc hướng giải quyết

- Bổ sung parser `_extract_json()` để lấy JSON từ response thường hoặc fenced code block.
- Nếu không parse được JSON, API trả về `raw_response` và thông báo lỗi rõ ràng để không làm hỏng demo.
- Tách dashboard logic vào `dashboard_service.py` để router gọn hơn.
- Recommendation đọc trực tiếp topic yếu active để đưa ra gợi ý ôn tập.
- Test các API không phụ thuộc Gemini bằng FastAPI TestClient.
- Viết lại Streamlit UI sạch UTF-8 để hiển thị tiếng Việt tốt hơn.
- Viết bộ câu hỏi đánh giá 20 câu và file tiêu chí đánh giá riêng để phục vụ báo cáo cuối.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong tuần này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ góp ý bộ câu hỏi đánh giá đã đủ đại diện cho nội dung demo hay chưa.
- Hỗ trợ góp ý tiêu chí chấm điểm thủ công: Accuracy, Faithfulness, Relevance, Citation và Hallucination.
- Hỗ trợ xác nhận bảng so sánh RAG vs LLM thường có thể dùng số liệu chấm thủ công ban đầu hay cần test thêm.
- Hỗ trợ góp ý demo flow cuối để trình bày trong buổi bảo vệ.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **5/5**

```text
1    2    3    4    [5]
```

Đến tuần 8, hệ thống đã có đầy đủ các phần chính của một sản phẩm demo: upload tài liệu, RAG chatbot, cá nhân hóa nhẹ, topic yếu, quiz, recommendation, dashboard và bộ đánh giá. Dù vẫn còn hạn chế về quota LLM và mức cá nhân hóa chưa quá sâu, sản phẩm đã đủ luồng để trình bày ý tưởng và minh chứng kết quả thực hiện trong quá trình thực tập.

### Kế hoạch làm việc tiếp theo

- Chuẩn bị slide/demo flow cho buổi báo cáo.
- Chụp minh chứng giao diện Streamlit đầy đủ các bước.
- Chụp minh chứng Swagger các endpoint chính.
- Chạy thử lại toàn bộ flow từ upload đến dashboard.
- Hoàn thiện nội dung báo cáo thực tập.
- Chấm thử bộ câu hỏi đánh giá và cập nhật số liệu so sánh nếu có thời gian.
- Kiểm tra lại API key/quota Gemini trước khi demo.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 8_Quiz_Dashboard_Evaluation_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh code `quiz_result.py`.
- Ảnh code `quiz_generator.py`.
- Ảnh Swagger endpoint `POST /quiz/generate`.
- Ảnh Swagger endpoint `POST /quiz/submit`.
- Ảnh bảng `quiz_results` trong database.
- Ảnh giao diện tạo quiz và nộp kết quả.
- Ảnh dashboard học tập trên Streamlit.
- Ảnh file `data/eval/eval_questions.csv`.
- Ảnh file `docs/evaluation_plan.md`.
- Ảnh README GitHub sau khi hoàn thiện.
- Ảnh commit GitHub tuần 8.

