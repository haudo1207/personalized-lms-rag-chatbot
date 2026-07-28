# Minh chứng tuần 7 - Nhật ký 2

## Nội dung minh chứng

Phần này minh chứng cho các công việc:

- Phát hiện topic yếu.
- Xây dựng user profile.
- Prompt cá nhân hóa.
- Pipeline Personalized RAG.
- API profile/weak topics.
- Streamlit hiển thị thông tin cá nhân hóa.

## File code cần chụp

### 1. Weak topic detector

File:

```text
backend/services/weak_topic_detector.py
```

Minh chứng cần chụp:

- Hàm `detect_weak_topic(...)`.
- Điều kiện bỏ qua topic `"Khác"`.
- Query đếm số lần hỏi cùng topic.
- Điều kiện `count >= threshold`.
- Phần tạo `WeakTopic`.

Link local:

```text
D:\DoHau_TTNN\rag-learning-chatbot\backend\services\weak_topic_detector.py
```

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/services/weak_topic_detector.py
```

### 2. User profile

File:

```text
backend/services/personalization.py
```

Minh chứng cần chụp:

- Hàm `get_recent_questions`.
- Hàm `get_weak_topics`.
- Hàm `build_user_profile`.
- Các trường `full_name`, `level`, `recent_questions`, `weak_topics`.

Link local:

```text
D:\DoHau_TTNN\rag-learning-chatbot\backend\services\personalization.py
```

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/services/personalization.py
```

### 3. Prompt cá nhân hóa

File:

```text
backend/services/prompt_template.py
```

Minh chứng cần chụp:

- Hàm `build_personalized_rag_prompt`.
- Phần thông tin người học.
- Quy tắc beginner/advanced.
- Quy tắc giải thích kỹ hơn nếu câu hỏi liên quan topic yếu.
- Quy tắc chỉ trả lời dựa trên tài liệu tham khảo.

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/services/prompt_template.py
```

### 4. Personalized RAG pipeline

File:

```text
backend/services/rag_pipeline.py
```

Minh chứng cần chụp:

- Hàm `ask_personalized_rag`.
- Bước retrieve chunks.
- Bước format context.
- Bước build personalized prompt.
- Bước generate answer.
- Response gồm `answer`, `sources`, `latency`.

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/services/rag_pipeline.py
```

### 5. API Chat/Profile/Weak Topics

File:

```text
backend/routers/chat.py
```

Minh chứng cần chụp:

- `POST /chat/` dùng `ask_personalized_rag`.
- Gọi `build_user_profile`.
- Gọi `detect_weak_topic`.
- Endpoint `GET /chat/profile/{user_id}/{course_id}`.
- Endpoint `GET /chat/weak-topics/{user_id}/{course_id}`.

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/backend/routers/chat.py
```

### 6. Giao diện Streamlit

File:

```text
app/streamlit_app.py
```

Minh chứng cần chụp:

- UI hiển thị topic của câu hỏi.
- UI hiển thị weak topic nếu có.
- Expander “Thông tin cá nhân hóa đã dùng”.
- Các trường level, weak topics, recent questions.

Link GitHub:

```text
https://github.com/haudo1207/personalized-lms-rag-chatbot/blob/main/app/streamlit_app.py
```

## Minh chứng API nên chụp

### Xem user profile

Endpoint:

```text
GET /chat/profile/1/1
```

Kết quả cần thấy:

```json
{
  "user_id": 1,
  "full_name": "...",
  "level": "beginner",
  "recent_questions": [],
  "weak_topics": []
}
```

### Xem weak topics

Endpoint:

```text
GET /chat/weak-topics/1/1
```

Kết quả cần thấy:

```json
[
  {
    "user_id": 1,
    "course_id": 1,
    "topic": "SQL JOIN",
    "reason": "Sinh viên hỏi cùng một chủ đề từ 3 lần trở lên.",
    "status": "active"
  }
]
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

- Ảnh code `weak_topic_detector.py`.
- Ảnh code `personalization.py`.
- Ảnh code prompt cá nhân hóa.
- Ảnh code `ask_personalized_rag`.
- Ảnh Swagger endpoint `GET /chat/profile/1/1`.
- Ảnh Swagger endpoint `GET /chat/weak-topics/1/1`.
- Ảnh Streamlit hiển thị topic/profile cá nhân hóa.
- Ảnh commit GitHub tuần 7.

