# Báo cáo thực tập tuần 7

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Xây dựng chức năng phân loại topic câu hỏi tại `backend/services/topic_classifier.py`.
- Bổ sung nhận diện các topic: Khóa chính, Khóa ngoại, SQL JOIN, Chuẩn hóa cơ sở dữ liệu, ERD và Khác.
- Cải thiện classifier bằng cách normalize tiếng Việt để nhận diện được cả câu có dấu và không dấu.
- Lưu topic đã phân loại vào bảng `chat_history`.
- Chuyển model `WeakTopic` từ placeholder sang SQLAlchemy model thật.
- Bổ sung bảng `weak_topics` để lưu các chủ đề sinh viên còn yếu.
- Xây dựng service `detect_weak_topic()` để phát hiện topic yếu khi sinh viên hỏi cùng một topic từ 3 lần trở lên.
- Xây dựng service cá nhân hóa tại `backend/services/personalization.py`.
- Tạo user profile gồm level, recent questions và weak topics.
- Bổ sung prompt RAG cá nhân hóa tại `backend/services/prompt_template.py`.
- Bổ sung pipeline `ask_personalized_rag()` để dùng user profile khi sinh câu trả lời.
- Cập nhật API `POST /chat/` để dùng personalized RAG, trả thêm topic, weak topic và user profile.
- Thêm API xem profile và topic yếu:
  - `GET /chat/profile/{user_id}/{course_id}`
  - `GET /chat/weak-topics/{user_id}/{course_id}`
- Cập nhật Streamlit để hiển thị topic, weak topic và thông tin cá nhân hóa đã dùng.
- Kiểm thử classifier, weak topic detector và route profile/weak topics.
- Commit và push mã nguồn tuần 7 lên GitHub.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách xây dựng topic classifier đơn giản bằng keyword để dễ giải thích trong báo cáo.
- Áp dụng normalize tiếng Việt để giảm lỗi khi người dùng nhập câu hỏi có dấu/không dấu.
- Biết cách mở rộng chat history để lưu thêm metadata phục vụ cá nhân hóa.
- Áp dụng SQLAlchemy để tạo model `WeakTopic` và truy vấn topic yếu theo user/course.
- Hiểu cách phát hiện dấu hiệu học yếu dựa trên hành vi hỏi lặp lại một chủ đề.
- Biết cách xây dựng user profile từ dữ liệu lịch sử học tập.
- Biết cách đưa thông tin người học vào prompt RAG để điều chỉnh cách trả lời theo beginner/advanced.
- Hiểu hơn về sự khác nhau giữa RAG thông thường và Personalized RAG.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **9/10**

Lý do:

- Đã hoàn thành đầy đủ các thành phần cá nhân hóa nhẹ theo kế hoạch.
- Topic classifier, lưu topic, weak topic detector, user profile và prompt cá nhân hóa đều đã hoạt động.
- Đã có API và UI để minh chứng kết quả.
- Chưa chấm 10/10 vì cá nhân hóa mới ở mức rule-based/keyword, chưa dùng mô hình học máy nâng cao.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    8    [9]    10
```

### Khó khăn/vướng mắc gặp phải

- Các file placeholder ban đầu có lỗi encoding tiếng Việt, cần thay bằng nội dung UTF-8 sạch.
- Nếu chỉ so khớp keyword thông thường, câu hỏi không dấu như "khoa chinh la gi" có thể không được phân loại đúng.
- Cần đảm bảo việc phát hiện topic yếu không tạo trùng nhiều bản ghi active cho cùng user/course/topic.
- Cần nối cá nhân hóa vào pipeline mà vẫn giữ được `ask_rag()` cũ để tránh ảnh hưởng các phần đã làm trước đó.

### Cách xử lý hoặc hướng giải quyết

- Viết lại các service tuần 7 bằng UTF-8 sạch.
- Thêm hàm `_normalize()` dùng `unicodedata` để bỏ dấu tiếng Việt và chuyển `đ` thành `d`.
- Detector kiểm tra topic yếu đang active trước khi tạo mới.
- Tách hàm `_build_sources()` trong RAG pipeline để dùng chung cho RAG thường và Personalized RAG.
- Kiểm thử classifier bằng nhiều câu hỏi mẫu: khóa chính, khóa ngoại, SQL JOIN, chuẩn hóa, ERD và câu ngoài chủ đề.
- Kiểm thử weak topic detector bằng SQLite in-memory.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong tuần này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ góp ý xem cách phát hiện topic yếu theo số lần hỏi lặp lại có phù hợp để trình bày trong báo cáo không.
- Hỗ trợ góp ý cách mô tả cá nhân hóa ở mức nhẹ, tránh trình bày quá mức so với phạm vi thực hiện.
- Hỗ trợ xác nhận các topic trong classifier đã đủ phù hợp với tài liệu demo môn cơ sở dữ liệu hay cần bổ sung thêm.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Tuần này hệ thống đã khác hơn so với một chatbot hỏi đáp tài liệu thông thường. Việc lưu topic, phát hiện topic yếu và dùng user profile giúp hệ thống có định hướng cá nhân hóa rõ hơn. Tuy cá nhân hóa vẫn còn đơn giản, đây là nền tảng hợp lý để giải thích trong báo cáo và mở rộng sau này.

### Kế hoạch làm việc tiếp theo

- Xây dựng chức năng sinh quiz từ tài liệu.
- Lưu kết quả làm quiz của sinh viên.
- Gợi ý ôn tập dựa trên topic yếu.
- Xây dựng dashboard học tập đơn giản.
- Chuẩn bị bộ câu hỏi đánh giá và bảng so sánh RAG với LLM thông thường.
- Hoàn thiện README và demo flow cuối.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 7_Personalization_WeakTopic_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh code `topic_classifier.py`.
- Ảnh code `weak_topic_detector.py`.
- Ảnh code `personalization.py`.
- Ảnh code prompt cá nhân hóa trong `prompt_template.py`.
- Ảnh Swagger/API trả về topic và user profile khi chat.
- Ảnh endpoint xem weak topics.
- Ảnh giao diện Streamlit hiển thị topic/profile cá nhân hóa.
- Ảnh commit GitHub tuần 7.

