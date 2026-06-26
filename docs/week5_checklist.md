# Checklist tuần 5

## Mục tiêu

- [x] Cài Gemini SDK.
- [x] Cấu hình `GEMINI_API_KEY` từ `.env`.
- [x] Viết LLM service gọi Gemini.
- [x] Viết prompt RAG có quy tắc không bịa thông tin.
- [x] Viết RAG pipeline: question -> retriever -> context -> prompt -> LLM -> answer + sources.
- [x] Viết Chat API `POST /chat/`.
- [x] Lưu chat history vào SQLite.
- [x] Viết API xem lịch sử chat `GET /chat/history/{user_id}`.
- [ ] Test Gemini sinh câu trả lời thành công bằng API key thật.
- [ ] Chụp ảnh Swagger hỏi đáp có nguồn.
- [ ] Chụp ảnh câu hỏi ngoài tài liệu bị từ chối.
- [ ] Chụp ảnh database có `chat_history`.

## API chat

```text
POST /chat/
```

Payload mẫu:

```json
{
  "user_id": 1,
  "course_id": 1,
  "question": "Khóa chính là gì?",
  "top_k": 5
}
```

Kết quả mong đợi:

```json
{
  "chat_id": 1,
  "answer": "...",
  "sources": [
    {
      "document_name": "database_chapter_1.txt",
      "page": 1,
      "content": "...",
      "distance": 0.12
    }
  ],
  "latency": 2.31
}
```

## Ghi chú

Nếu thiếu hoặc sai `GEMINI_API_KEY`, API chat sẽ trả `503` với thông báo cấu hình rõ ràng thay vì làm backend crash.

Model mặc định đang dùng: `gemini-2.0-flash`. Model `gemini-1.5-flash` trong kế hoạch ban đầu không còn xuất hiện trong danh sách model hỗ trợ `generateContent` của tài khoản/API hiện tại.

Đã kiểm tra Gemini API thật:

- `gemini-1.5-flash`: API trả `404 NotFound`.
- `gemini-2.0-flash`: model hợp lệ nhưng API trả `429 ResourceExhausted` vì quota free tier hiện tại bằng `0`.

Vì vậy pipeline RAG, Chat API và lưu lịch sử đã test được bằng mock LLM; phần sinh câu trả lời thật cần API key/quota Gemini khả dụng.
