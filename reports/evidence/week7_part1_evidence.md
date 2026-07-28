# Minh chứng tuần 7 - Nhật ký 1

## Nội dung minh chứng

Phần này minh chứng cho các công việc:

- Tạo topic classifier.
- Nhận diện các topic: Khóa chính, Khóa ngoại, SQL JOIN, Chuẩn hóa cơ sở dữ liệu, ERD, Khác.
- Lưu topic vào `chat_history`.
- Tạo model `WeakTopic`.

## File code cần chụp

### 1. Topic classifier

File:

```text
backend/services/topic_classifier.py
```

Minh chứng cần chụp:

- Hàm `classify_topic(question: str)`.
- Hàm normalize tiếng Việt `_normalize(text: str)`.
- Các keyword phân loại topic.

Link local:

```text
D:\DoHau_TTNN\rag-learning-chatbot\backend\services\topic_classifier.py
```

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/services/topic_classifier.py
```

### 2. Lưu topic vào chat history

File:

```text
backend/routers/chat.py
```

Minh chứng cần chụp:

- Dòng import `classify_topic`.
- Dòng `topic = classify_topic(request.question)`.
- Phần tạo `ChatHistory(..., topic=topic, ...)`.
- Response trả thêm `"topic": topic`.

Link local:

```text
D:\DoHau_TTNN\rag-learning-chatbot\backend\routers\chat.py
```

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/routers/chat.py
```

### 3. Model WeakTopic

File:

```text
backend/models/weak_topic.py
```

Minh chứng cần chụp:

- Class `WeakTopic(Base)`.
- Tên bảng `weak_topics`.
- Các cột `user_id`, `course_id`, `topic`, `reason`, `status`, `created_at`.

Link local:

```text
D:\DoHau_TTNN\rag-learning-chatbot\backend\models\weak_topic.py
```

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/models/weak_topic.py
```

### 4. Import model vào main.py

File:

```text
backend/main.py
```

Minh chứng cần chụp:

- Dòng import `WeakTopic`.
- Phần `Base.metadata.create_all(bind=engine)`.

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/main.py
```

## Minh chứng test nên chụp

### Test classifier

Có thể chạy:

```powershell
.\venv\Scripts\python.exe -c "from backend.services.topic_classifier import classify_topic; print(classify_topic('Khóa chính là gì?')); print(classify_topic('foreign key dùng để làm gì?')); print(classify_topic('INNER JOIN khác LEFT JOIN thế nào?'))"
```

Kết quả kỳ vọng:

```text
Khóa chính
Khóa ngoại
SQL JOIN
```

## Commit GitHub

Commit tuần 7:

```text
e07711d week 7 add personalization weak topic detection
```

Link commit:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/commit/e07711d
```

## Gợi ý ảnh nộp

- Ảnh file `topic_classifier.py`.
- Ảnh file `chat.py` đoạn classify topic và lưu `topic`.
- Ảnh file `weak_topic.py`.
- Ảnh terminal test classifier.
- Ảnh commit GitHub tuần 7.

