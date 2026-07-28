# Báo cáo thực tập tuần 7 - Nhật ký 2

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Xây dựng service `backend/services/weak_topic_detector.py`.
- Cài đặt logic phát hiện topic yếu khi sinh viên hỏi cùng một topic từ 3 lần trở lên.
- Kiểm tra topic yếu đang active trước khi tạo mới để tránh trùng dữ liệu.
- Xây dựng service cá nhân hóa tại `backend/services/personalization.py`.
- Tạo user profile gồm `user_id`, `full_name`, `level`, `recent_questions` và `weak_topics`.
- Bổ sung prompt cá nhân hóa tại `backend/services/prompt_template.py`.
- Thêm quy tắc trả lời khác nhau cho người học beginner và advanced.
- Thêm quy tắc giải thích kỹ hơn nếu câu hỏi liên quan đến topic yếu.
- Bổ sung pipeline `ask_personalized_rag()` trong `backend/services/rag_pipeline.py`.
- Cập nhật API `POST /chat/` để dùng personalized RAG.
- Trả thêm `topic`, `weak_topic` và `user_profile` trong response chat.
- Thêm API xem profile và weak topics:
  - `GET /chat/profile/{user_id}/{course_id}`
  - `GET /chat/weak-topics/{user_id}/{course_id}`
- Cập nhật Streamlit để hiển thị topic, weak topic và profile cá nhân hóa đã dùng.
- Kiểm thử weak topic detector bằng SQLite in-memory.
- Kiểm thử route profile/weak topics bằng FastAPI TestClient.
- Commit và push mã nguồn tuần 7 lên GitHub.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách phát hiện dấu hiệu học yếu dựa trên hành vi hỏi lặp lại cùng một chủ đề.
- Biết cách xây dựng user profile từ dữ liệu đã lưu trong database.
- Hiểu cách đưa thông tin người học vào prompt RAG để cá nhân hóa câu trả lời.
- Biết cách giữ lại RAG pipeline cũ và bổ sung pipeline mới mà không phá các chức năng đã hoàn thành.
- Áp dụng TestClient và SQLite in-memory để kiểm thử logic backend không phụ thuộc LLM.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **9/10**

Lý do:

- Đã hoàn thành đầy đủ các thành phần chính của cá nhân hóa nhẹ.
- Có weak topic detector, user profile, personalized prompt, API và UI minh chứng.
- Chưa chấm 10/10 vì cá nhân hóa vẫn ở mức rule-based, chưa dùng mô hình học nâng cao.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    8    [9]    10
```

### Khó khăn/vướng mắc gặp phải

- Cần quyết định thời điểm gọi weak topic detector để số lần hỏi được tính đúng.
- Cần tránh tạo nhiều bản ghi weak topic giống nhau cho cùng user/course/topic.
- Prompt cá nhân hóa phải rõ ràng nhưng không được khiến LLM trả lời ngoài tài liệu.
- Việc test câu trả lời personalized thật vẫn phụ thuộc API key/quota Gemini.

### Cách xử lý hoặc hướng giải quyết

- Gọi weak topic detector sau khi lưu chat record để lần hỏi hiện tại được tính vào tổng số.
- Kiểm tra bản ghi weak topic active trước khi tạo mới.
- Giữ quy tắc bắt buộc trong prompt: chỉ trả lời dựa trên tài liệu tham khảo.
- Test phần classifier, profile và detector độc lập để không phụ thuộc Gemini.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong giai đoạn này.

### Bạn cần GVHD hỗ trợ gì không

- Góp ý cách định nghĩa “topic yếu” dựa trên số lần hỏi lặp lại đã hợp lý chưa.
- Góp ý cách trình bày personalized RAG trong báo cáo để đúng với phạm vi thực hiện.
- Hỗ trợ xác nhận cần demo beginner/advanced bằng user thật hay có thể minh chứng bằng response prompt/API.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Sau giai đoạn này, hệ thống đã có điểm khác biệt so với chatbot PDF thông thường. Chatbot không chỉ trả lời dựa trên tài liệu mà còn biết topic câu hỏi, ghi nhận lịch sử học tập và tạo nền tảng để cá nhân hóa câu trả lời theo người học.

### Kế hoạch làm việc tiếp theo

- Xây dựng chức năng sinh quiz từ tài liệu.
- Lưu kết quả làm quiz.
- Gợi ý ôn tập theo weak topics.
- Xây dựng dashboard học tập đơn giản.
- Chuẩn bị bộ câu hỏi đánh giá và README hoàn chỉnh.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 7_NhatKy2_PersonalizedRAG_WeakTopic_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh code `weak_topic_detector.py`.
- Ảnh code `personalization.py`.
- Ảnh prompt cá nhân hóa trong `prompt_template.py`.
- Ảnh response `POST /chat/` có topic/user_profile.
- Ảnh endpoint xem weak topics.
- Ảnh giao diện Streamlit hiển thị thông tin cá nhân hóa.
- Ảnh commit GitHub tuần 7.

