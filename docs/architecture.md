# Kiến trúc hệ thống

## Sơ đồ tổng quan

```text
Student
  |
  v  (JWT Bearer token)
Streamlit Frontend (app/)
  |
  v
FastAPI Backend (backend/main.py)
  |
  |-- Auth (JWT + bcrypt)
  |-- User Service
  |-- Course Service (ownership-based: 1 course = 1 owner)
  |-- Document Service
  |-- Retrieval Service
  |-- Chat Service
  |-- Quiz Service
  |-- Dashboard Service
  |
  v
AI Service Layer (backend/services/)
  |
  |-- Document Loader + Text Cleaner
  |-- Chunking (semantic, percentile breakpoint + fixed-size fallback)
  |-- Embedding Service (sentence-transformers)
  |-- Vector Store (ChromaDB)
  |-- BM25 (lexical, tiếng Việt)
  |-- Retriever (Hybrid RRF fusion + on-demand Query Decomposition / Multi-Query)
  |-- Reranker (Cross-Encoder)
  |-- RAG Pipeline (query reformulation, lost-in-middle reorder, prompt build)
  |-- Personalization (user profile: level, recent questions, weak topics)
  |-- Topic Taxonomy (per-course KMeans clustering + LLM labeling)
  |-- Weak Topic Detector (weighted formula)
  |-- Quiz Generator (adaptive difficulty)
  |-- Recommendation (LLM, grounded in course content)
  |-- Question Suggester
  |
  v
SQLite (SQLAlchemy + Alembic) + ChromaDB
```

## Xác thực và phân quyền

1. Đăng nhập (`/auth/login`) trả về JWT access token (`python-jose`, HS256), mật khẩu hash bằng bcrypt (`passlib`).
2. Mỗi request tới các endpoint còn lại đi kèm `Authorization: Bearer <token>`, giải mã bởi `backend/security_deps.py`.
3. Mô hình course theo quyền sở hữu (ownership-based): mỗi course có `owner_id` là một sinh viên, không có bước "enroll" và không có UI quản trị riêng cho sinh viên. `role` (`student`/`admin`) vẫn tồn tại ở tầng backend: admin có quyền ghi đè toàn hệ thống (hỗ trợ/debug), nhưng không xuất hiện như một luồng nghiệp vụ dành cho sinh viên.

## Luồng xử lý tài liệu

1. Sinh viên upload PDF/DOCX/TXT từ giao diện Streamlit.
2. Backend lưu file gốc và metadata tài liệu vào SQLite.
3. Document Loader đọc nội dung theo trang (PDF/TXT) hoặc theo toàn văn (DOCX).
4. Text Cleaner chuẩn hóa văn bản: loại dòng chấm mục lục, dòng watermark từ trang chia sẻ tài liệu.
5. Chunking chia nội dung mỗi trang thành các đoạn theo ngữ nghĩa: tách câu tiếng Việt (`underthesea`), nhóm các câu liền kề có khoảng cách embedding nhỏ hơn ngưỡng percentile (đã tinh chỉnh bằng thực nghiệm — xem `reports/eval/percentile_sweep_table.md`); nhóm quá dài fallback về chia cố định có overlap.
6. Embedding Service tạo vector cho từng chunk (sentence-transformers đa ngôn ngữ).
7. Vector Store lưu vector và metadata vào ChromaDB; toàn bộ bước 3–7 chạy trong một lần gọi `/documents/upload`.
8. Sau khi index xong, hệ thống sinh taxonomy chủ đề cho course (nếu course chưa có) để phục vụ phân loại topic câu hỏi ở luồng hỏi đáp — lỗi ở bước này không làm fail upload.

## Luồng hỏi đáp

1. Sinh viên nhập câu hỏi.
2. Câu hỏi được viết lại (reformulate) dựa trên 3 lượt hội thoại gần nhất, để câu hỏi ngắn/nối tiếp ("còn cái kia thì sao?") thành câu hỏi độc lập trước khi truy xuất.
3. Retriever truy xuất Hybrid: Dense (ChromaDB) + BM25 tiếng Việt, hợp nhất bằng Reciprocal Rank Fusion (RRF).
4. Nếu câu hỏi có dấu hiệu so sánh/nhiều phần (heuristic regex rẻ, không gọi LLM), Query Decomposition tách thành các câu hỏi con trước khi fusion. Nếu điểm rerank của kết quả top-1 ở lượt đầu thấp hơn ngưỡng tin cậy, hệ thống mới gọi thêm Multi-Query (LLM sinh biến thể câu hỏi) và truy xuất lại — cả hai kỹ thuật này chỉ tốn thêm LLM khi thật sự cần ("on-demand routing"), mặc định tắt hoàn toàn để giữ latency thấp cho phần lớn câu hỏi.
5. Reranker (Cross-Encoder) xếp hạng lại Top-K trước khi đưa vào prompt.
6. Ngữ cảnh được sắp lại theo thứ tự chống hiệu ứng "lost in the middle" (kết quả liên quan nhất đặt ở hai đầu ngữ cảnh).
7. RAG Pipeline ghép câu hỏi, ngữ cảnh và prompt cá nhân hóa.
8. LLM Service gọi Gemini API để sinh câu trả lời kèm nguồn trích dẫn (tên tài liệu + số trang); trả lời "không đủ thông tin" nếu ngữ cảnh không phù hợp.
9. Backend lưu lịch sử hỏi đáp, phân loại topic câu hỏi (so khớp cosine similarity với taxonomy riêng của course, không gọi LLM mỗi câu hỏi) và cập nhật weak topic nếu cần.
10. Frontend hiển thị câu trả lời kèm nguồn trích dẫn, cho phép feedback 👍/👎.

## Luồng cá nhân hóa

1. Hệ thống theo dõi lịch sử hỏi đáp và kết quả quiz theo từng (user, course).
2. Weak Topic Detector tính điểm yếu theo công thức trọng số: `0.4 × tần suất hỏi + 0.4 × mức yếu điểm quiz + 0.2 × mức học dồn dập (cramming)`; vượt ngưỡng thì đánh dấu topic đang yếu (dưới ngưỡng thì tự động chuyển trạng thái "resolved").
3. Quiz Generator sinh quiz trắc nghiệm từ chính nội dung tài liệu đã index; độ khó tự thích ứng theo điểm quiz gần nhất của người học ở topic đó. Đáp án đúng chỉ lưu server-side; `/quiz/submit` chấm theo phiên đã lưu, mỗi phiên chỉ nộp một lần và có hạn sử dụng.
4. Recommendation sinh gợi ý học tiếp cho từng topic yếu, dựa trên cùng pipeline retrieval của course đó (không phải template cố định), có cache theo mức độ yếu để không gọi LLM lại mỗi lần xem dashboard.
5. Dashboard tổng hợp: tổng số câu hỏi, câu hỏi theo topic, danh sách topic yếu, lịch sử điểm quiz, tỉ lệ feedback 👍/👎.
