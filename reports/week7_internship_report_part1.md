# Báo cáo thực tập tuần 7 - Nhật ký 1

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Nghiên cứu yêu cầu cá nhân hóa nhẹ cho hệ thống chatbot học tập.
- Xác định các topic cần phân loại trong phạm vi demo: Khóa chính, Khóa ngoại, SQL JOIN, Chuẩn hóa cơ sở dữ liệu, ERD và Khác.
- Xây dựng service `backend/services/topic_classifier.py`.
- Cài đặt cơ chế phân loại topic bằng keyword để dễ giải thích trong báo cáo.
- Bổ sung bước normalize tiếng Việt để nhận diện được cả câu hỏi có dấu và không dấu.
- Tích hợp topic classifier vào API `POST /chat/`.
- Lưu topic đã phân loại vào bảng `chat_history`.
- Chuyển model `WeakTopic` từ placeholder sang SQLAlchemy model thật tại `backend/models/weak_topic.py`.
- Import `WeakTopic` vào `backend/main.py` để hệ thống tạo bảng `weak_topics`.
- Kiểm thử nhanh classifier với các câu hỏi mẫu về khóa chính, khóa ngoại, JOIN, chuẩn hóa và ERD.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách xây dựng topic classifier đơn giản bằng rule/keyword.
- Biết cách xử lý tiếng Việt có dấu bằng `unicodedata`.
- Hiểu cách lưu metadata của câu hỏi vào lịch sử chat để phục vụ phân tích học tập.
- Áp dụng SQLAlchemy để chuyển một model placeholder thành bảng dữ liệu thật.
- Hiểu cách thiết kế bảng `weak_topics` theo user, course, topic, reason và status.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **8/10**

Lý do:

- Đã hoàn thành phần phân loại topic và lưu topic vào lịch sử hỏi đáp.
- Đã chuẩn bị xong model dữ liệu cho weak topic.
- Chưa chấm cao hơn vì phần phát hiện topic yếu và prompt cá nhân hóa chưa hoàn thiện ở nhật ký này.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    [8]    9    10
```

### Khó khăn/vướng mắc gặp phải

- Nếu chỉ so khớp chuỗi tiếng Việt có dấu, hệ thống dễ bỏ sót câu hỏi không dấu.
- Một số file placeholder ban đầu có lỗi hiển thị tiếng Việt, cần viết lại sạch bằng UTF-8.
- Cần đảm bảo việc thêm `WeakTopic` không ảnh hưởng các model cũ đã có.

### Cách xử lý hoặc hướng giải quyết

- Viết hàm normalize để đưa câu hỏi về dạng không dấu, chữ thường.
- Dùng danh sách keyword rõ ràng, phù hợp với phạm vi tài liệu demo.
- Kiểm tra classifier bằng nhiều câu hỏi mẫu trước khi nối vào chat API.
- Giữ topic mặc định là `Khác` nếu không phân loại được.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong giai đoạn này.

### Bạn cần GVHD hỗ trợ gì không

- Góp ý danh sách topic phân loại đã phù hợp với nội dung demo môn cơ sở dữ liệu hay chưa.
- Góp ý cách trình bày topic classifier keyword trong báo cáo sao cho rõ ràng, không phóng đại thành mô hình AI phức tạp.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Phần topic classifier tuy đơn giản nhưng là bước nền quan trọng để hệ thống có dữ liệu phục vụ cá nhân hóa. Sau khi topic được lưu vào `chat_history`, hệ thống có thể phân tích sinh viên thường hỏi về nội dung nào và từ đó phát hiện chủ đề còn yếu.

### Kế hoạch làm việc tiếp theo

- Xây dựng weak topic detector.
- Tạo user profile từ lịch sử câu hỏi và weak topics.
- Bổ sung prompt cá nhân hóa cho beginner/advanced.
- Cập nhật Streamlit để hiển thị topic và thông tin cá nhân hóa.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 7_NhatKy1_TopicClassifier_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh code `topic_classifier.py`.
- Ảnh code `weak_topic.py`.
- Ảnh `chat_history` có cột topic.
- Ảnh kết quả test classifier bằng các câu hỏi mẫu.

