# Báo cáo thực tập tuần 8 - Nhật ký 2

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Xây dựng service gợi ý ôn tập tại `backend/services/recommendation.py`.
- Gợi ý nội dung ôn tập dựa trên các weak topics đang active.
- Xây dựng dashboard service tại `backend/services/dashboard_service.py`.
- Tổng hợp dữ liệu dashboard gồm tổng số câu hỏi, topic yếu, kết quả quiz và điểm quiz trung bình.
- Thay router dashboard bằng endpoint `GET /dashboard/student/{user_id}?course_id=...`.
- Cập nhật Streamlit UI để có khu vực tạo quiz ôn tập.
- Bổ sung giao diện chọn đáp án và nộp kết quả quiz.
- Cập nhật Streamlit UI để hiển thị dashboard học tập cá nhân.
- Viết lại `README.md` sạch UTF-8, đầy đủ cách cài đặt, cách chạy, API chính và demo flow.
- Tạo bộ câu hỏi đánh giá tại `data/eval/eval_questions.csv` gồm 20 câu hỏi.
- Tạo tài liệu `docs/evaluation_plan.md` gồm tiêu chí chấm thủ công và bảng so sánh LLM only, RAG, Personalized RAG.
- Kiểm thử endpoint dashboard bằng FastAPI TestClient.
- Kiểm tra compile toàn bộ backend/app.
- Commit và push mã nguồn tuần 8 lên GitHub.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách xây dựng dashboard học tập đơn giản từ nhiều bảng dữ liệu.
- Biết cách thiết kế recommendation rule-based dựa trên weak topics.
- Biết cách đưa kết quả quiz vào dashboard để phản ánh tiến độ học tập.
- Biết cách xây dựng bộ câu hỏi đánh giá cho hệ thống RAG.
- Hiểu các tiêu chí đánh giá RAG: Accuracy, Faithfulness, Relevance, Citation và Hallucination.
- Biết cách trình bày bảng so sánh LLM only, RAG và Personalized RAG trong báo cáo.
- Củng cố kỹ năng viết README hoàn chỉnh cho một project demo.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **9/10**

Lý do:

- Đã hoàn thành recommendation, dashboard, UI quiz/dashboard, README và bộ đánh giá.
- Endpoint dashboard đã test thành công.
- Demo flow cuối đã rõ ràng.
- Chưa chấm 10/10 vì số liệu đánh giá hiện vẫn là mẫu ban đầu, cần chấm thủ công thêm nếu có thời gian.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    8    [9]    10
```

### Khó khăn/vướng mắc gặp phải

- Dashboard cần gom dữ liệu từ nhiều nguồn nên phải tách service để dễ quản lý.
- Cần viết UI quiz/dashboard sao cho không làm giao diện bị quá rối.
- Bộ câu hỏi đánh giá cần đủ đại diện cho các topic chính nhưng vẫn phù hợp thời gian demo.
- README cũ có lỗi hiển thị tiếng Việt nên cần viết lại.

### Cách xử lý hoặc hướng giải quyết

- Tách dashboard logic vào `dashboard_service.py`.
- Streamlit được chia thành các khu vực rõ ràng: tài liệu, chat/history, quiz/dashboard.
- Tạo bộ đánh giá tối thiểu 20 câu hỏi, tập trung vào các topic đã dùng trong demo.
- Viết `docs/evaluation_plan.md` để ghi rõ cách chấm và bảng so sánh mẫu.
- Viết lại README bằng UTF-8 sạch.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong giai đoạn này.

### Bạn cần GVHD hỗ trợ gì không

- Góp ý bộ câu hỏi đánh giá đã đủ tốt để đưa vào báo cáo chưa.
- Góp ý bảng so sánh RAG vs LLM thường có cần chạy thêm dữ liệu thực nghiệm không.
- Góp ý demo flow cuối trước khi trình bày bảo vệ.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **5/5**

```text
1    2    3    4    [5]
```

Đến cuối tuần 8, hệ thống đã có đủ các phần chính của một sản phẩm demo hoàn chỉnh: upload tài liệu, RAG chatbot, cá nhân hóa nhẹ, topic yếu, quiz, recommendation, dashboard và bộ đánh giá. Đây là giai đoạn giúp sản phẩm sẵn sàng hơn cho báo cáo và bảo vệ.

### Kế hoạch làm việc tiếp theo

- Chuẩn bị slide thuyết trình.
- Chụp minh chứng Swagger và Streamlit.
- Chạy thử toàn bộ flow demo.
- Hoàn thiện báo cáo thực tập.
- Nếu có thời gian, chấm thủ công bộ câu hỏi đánh giá để thay số liệu mẫu bằng số liệu thực tế.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 8_NhatKy2_Dashboard_Evaluation_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh code `recommendation.py`.
- Ảnh code `dashboard_service.py`.
- Ảnh Swagger endpoint dashboard.
- Ảnh giao diện dashboard Streamlit.
- Ảnh file `data/eval/eval_questions.csv`.
- Ảnh file `docs/evaluation_plan.md`.
- Ảnh README GitHub sau khi hoàn thiện.
- Ảnh commit GitHub tuần 8.

