# Kiến trúc hệ thống

## Sơ đồ tổng quan

```text
Student
  |
  v
Streamlit Frontend
  |
  v
FastAPI Backend
  |
  |-- User Service
  |-- Course Service
  |-- Document Service
  |-- Chat Service
  |-- Quiz Service
  |
  v
AI Service Layer
  |
  |-- Document Loader
  |-- Text Cleaner
  |-- Chunking
  |-- Embedding
  |-- Vector Store
  |-- Retriever
  |-- RAG Pipeline
  |-- Personalization
  |-- Topic Classifier
  |-- Weak Topic Detector
  |-- Quiz Generator
  |-- Recommendation
  |
  v
SQLite + ChromaDB
```

## Luồng xử lý tài liệu

1. Sinh viên upload PDF/DOCX/TXT từ giao diện Streamlit.
2. Backend lưu metadata tài liệu vào SQLite.
3. Document Loader đọc nội dung tài liệu.
4. Text Cleaner chuẩn hóa văn bản.
5. Chunking chia nội dung thành các đoạn nhỏ.
6. Embedding Service tạo vector cho từng chunk.
7. Vector Store lưu vector và metadata vào ChromaDB.

## Luồng hỏi đáp

1. Sinh viên nhập câu hỏi.
2. Retriever tìm các chunk liên quan trong ChromaDB.
3. RAG Pipeline ghép câu hỏi, ngữ cảnh và prompt.
4. LLM Service gọi Gemini API để sinh câu trả lời.
5. Backend lưu lịch sử hỏi đáp.
6. Frontend hiển thị câu trả lời kèm nguồn trích dẫn.

## Luồng cá nhân hóa

1. Hệ thống theo dõi lịch sử hỏi đáp và kết quả quiz.
2. Weak Topic Detector phát hiện topic người học thường sai hoặc hỏi nhiều.
3. Quiz Generator sinh câu hỏi ôn tập theo topic yếu.
4. Recommendation gợi ý nội dung nên học tiếp.

