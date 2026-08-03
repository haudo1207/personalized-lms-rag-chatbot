# RAG Learning Chatbot

Hệ thống chatbot hỏi đáp tài liệu học tập cho sinh viên sử dụng Retrieval-Augmented Generation (RAG), có xác thực JWT, mô hình course theo quyền sở hữu (ownership-based), hybrid search + reranker, cá nhân hóa nhẹ theo trình độ, phát hiện topic yếu, tạo quiz ôn tập thích ứng và dashboard học tập.

## Tên đề tài

**Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation.**

## Chức năng chính

**Xác thực & phân quyền**
- Đăng ký/đăng nhập bằng JWT (`python-jose`), mật khẩu hash bằng bcrypt (`passlib`).
- Mô hình course theo quyền sở hữu: mỗi course thuộc đúng một sinh viên (`owner_id`); không có bước "enroll". Admin giữ quyền ghi đè toàn hệ thống để hỗ trợ/debug nhưng không có UI riêng cho sinh viên.

**Tài liệu & chỉ mục**
- Upload PDF/DOCX/TXT, đọc – làm sạch (bỏ dòng chấm mục lục, watermark trang chia sẻ tài liệu) – chia chunk – tạo embedding – lưu vào ChromaDB, tất cả trong một lần gọi `/documents/upload`.
- Semantic chunking: tách câu tiếng Việt bằng `underthesea`, nhóm các câu liền kề có độ tương đồng embedding cao thành một chunk, breakpoint theo percentile khoảng cách (đã tinh chỉnh bằng thực nghiệm quét percentile — xem `reports/eval/percentile_sweep_table.md`); nhóm quá dài fallback về chia cố định 700 ký tự/overlap 100.
- Gợi ý câu hỏi mở đầu sinh từ chính nội dung tài liệu vừa upload (không suy diễn từ tên file).

**Truy xuất (Retrieval)**
- Hybrid Search: Dense (sentence-transformers đa ngôn ngữ) + BM25 tiếng Việt tự viết, hợp nhất bằng Reciprocal Rank Fusion (RRF).
- Re-rank Top-K bằng Cross-Encoder (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`).
- Viết lại câu hỏi (query reformulation) dựa trên 3 lượt hội thoại gần nhất trước khi truy xuất.
- Định tuyến on-demand, không tốn LLM khi không cần: Query Decomposition (tách câu hỏi so sánh) chỉ kích hoạt khi một heuristic regex rẻ (`query_router.is_complex_question`) nhận diện câu hỏi so sánh/nhiều phần; Multi-Query chỉ kích hoạt khi điểm rerank của kết quả top-1 ở lượt truy xuất đầu thấp hơn ngưỡng tin cậy đã calibrate.
- Sắp xếp lại ngữ cảnh chống hiệu ứng "lost in the middle" trước khi đưa vào prompt.

**Trả lời & cá nhân hóa**
- Gọi Gemini API sinh câu trả lời bám tài liệu, luôn kèm nguồn (tên tài liệu + số trang); trả lời "không đủ thông tin" khi ngữ cảnh không phù hợp, không bịa.
- Cá nhân hóa prompt theo trình độ (beginner/intermediate/advanced), câu hỏi gần đây và topic yếu của người học.
- Phân loại topic câu hỏi theo taxonomy riêng của từng course: nhãn chủ đề sinh một lần bằng KMeans-cluster toàn bộ chunk đã index + LLM đặt tên cụm, sau đó mỗi câu hỏi chỉ so khớp cosine similarity với các nhãn có sẵn (không tốn LLM mỗi câu hỏi).

**Học tập cá nhân hóa**
- Phát hiện topic yếu theo công thức trọng số: `0.4 × tần suất hỏi + 0.4 × mức yếu điểm quiz + 0.2 × mức học dồn dập (cramming)`.
- Sinh quiz trắc nghiệm từ chính nội dung tài liệu đã index; độ khó tự thích ứng theo điểm quiz gần nhất của người học; đáp án lưu server-side, `/quiz/submit` chấm theo phiên đã lưu (không tin điểm client tự tính), mỗi phiên chỉ nộp một lần và có hạn sử dụng.
- Gợi ý ôn tập theo topic yếu, sinh từ nội dung tài liệu thật qua cùng pipeline retrieval (không phải template cố định).
- Dashboard sinh viên: tổng số câu hỏi, số câu hỏi theo từng topic, danh sách topic yếu, lịch sử điểm quiz, tỉ lệ feedback 👍/👎.

## Công nghệ sử dụng

- Python, FastAPI, Streamlit
- SQLite + SQLAlchemy (schema tạo bằng `Base.metadata.create_all()`, không dùng migration tool)
- ChromaDB (vector store)
- Sentence-Transformers (embedding đa ngôn ngữ + Cross-Encoder reranker)
- underthesea (tách câu tiếng Việt), scikit-learn (KMeans clustering)
- Gemini API (google-generativeai)
- PyMuPDF, python-docx
- python-jose (JWT), passlib/bcrypt (hash mật khẩu)
- Git/GitHub

## Cấu trúc thư mục

```text
backend/
  models/          SQLAlchemy models (User, Course, Document, ChatHistory,
                    CourseTopic, QuizSession, QuizResult, WeakTopic)
  routers/         FastAPI routers (auth, users, courses, documents,
                    retrieval, chat, quiz, dashboard)
  services/        chunking, embedding, vector_store, bm25, reranker,
                    retriever (hybrid + on-demand routing), rag_pipeline,
                    query_decomposition/query_expansion/query_router,
                    personalization, topic_taxonomy, weak_topic_detector,
                    quiz_generator, recommendation, dashboard_service,
                    question_suggester, document_loader, text_cleaner,
                    auth_service, llm_service, prompt_template
  security_deps.py JWT auth + ownership/role dependency checks
  config.py        Settings (.env)
app/
  streamlit_app.py Streamlit UI entrypoint (login + navigation)
  pages/           home, chat, documents, quiz, analytics, settings
  api_client.py    HTTP client thuần Python gọi backend (không phụ thuộc Streamlit)
data/
  raw/             Tài liệu gốc (PDF giáo trình dùng để demo/ingest)
  processed/       Tài liệu đã làm sạch (txt)
  eval/            Bộ câu hỏi + gold chunk dùng để đánh giá retrieval
docs/              Tài liệu phạm vi, kiến trúc, kế hoạch đánh giá
reports/eval/      Kết quả đánh giá retrieval + generation (số liệu thật)
scripts/           Ingest corpus, seed tài khoản demo, đánh giá retrieval/generation,
                   sweep tham số chunking, smoke test frontend
tests/             pytest (70 test, xem mục Đánh giá)
vector_store/      ChromaDB local (bỏ qua khỏi Git)
```

## Cài đặt

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Tạo file `.env` từ `.env.example`:

```env
GEMINI_API_KEY=your_real_api_key
GEMINI_MODEL=gemini-2.5-flash
JWT_SECRET=change-me-to-a-long-random-string-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=720
```

Tạo schema DB và 2 tài khoản demo (chạy một lần):

```powershell
python scripts/seed_auth.py
```

Tài khoản demo được tạo: `admin@edu.ai` / `Admin@123` và `student@edu.ai` / `Student@123`.

## Chạy backend

```powershell
uvicorn backend.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs` · Health check: `http://127.0.0.1:8000/health`

## Chạy giao diện Streamlit

```powershell
streamlit run app/streamlit_app.py
```

URL mặc định: `http://127.0.0.1:8501`. Đăng nhập bằng tài khoản demo ở trên trước khi dùng các trang chức năng.

## API chính

### Auth
- `POST /auth/login`: đăng nhập, trả JWT access token.
- `POST /auth/change-password`: tự đổi mật khẩu (chỉ cho chính mình).

### Users
- `POST /users/`, `GET /users/`: tạo/xem danh sách user (chỉ admin).
- `PATCH /users/{user_id}/level`: đổi trình độ học tập.

### Courses
- `POST /courses/`: tạo course, người tạo là owner.
- `GET /courses/mine`: course của chính mình. `GET /courses/`: toàn bộ course (chỉ admin).
- `PATCH /courses/{course_id}`, `DELETE /courses/{course_id}`: chỉ owner hoặc admin; xoá là xoá cứng, cascade toàn bộ tài liệu/chunk/lịch sử chat/quiz/topic yếu của course.

### Documents
- `POST /documents/upload`: upload, chunk, embedding và index trong một lần gọi.
- `POST /documents/{document_id}/index`: thử index lại tài liệu bị lỗi (không nằm trong luồng chính).
- `GET /documents/`, `GET /documents/suggested-questions`, `PATCH /documents/{document_id}`, `DELETE /documents/{document_id}`, `GET /documents/{document_id}/download`.

### Retrieval
- `POST /retrieval/search`: chỉ truy xuất chunk liên quan, không gọi LLM.

### Chat
- `POST /chat/`: hỏi chatbot RAG cá nhân hóa.
- `GET /chat/history/{user_id}`, `DELETE /chat/history/{user_id}/{course_id}`.
- `GET /chat/profile/{user_id}/{course_id}`, `GET /chat/weak-topics/{user_id}/{course_id}`.
- `PATCH /chat/{chat_id}/feedback`: gửi 👍/👎 cho một câu trả lời.

### Quiz
- `POST /quiz/generate`: sinh quiz từ tài liệu, độ khó tự thích ứng.
- `POST /quiz/submit`: chấm điểm theo phiên đã lưu server-side.
- `GET /quiz/results/{user_id}`.

### Dashboard
- `GET /dashboard/student/{user_id}?course_id=1`: dashboard học tập cá nhân + gợi ý ôn tập.

## Demo flow

1. Chạy FastAPI backend, chạy Streamlit UI.
2. Đăng nhập bằng tài khoản demo (admin hoặc student).
3. Vào Trang chủ, tạo/chọn course.
4. Upload tài liệu học tập.
5. Vào Chat AI, hỏi chatbot, kiểm tra câu trả lời và nguồn trích dẫn.
6. Hỏi cùng một topic nhiều lần để phát hiện weak topic.
7. Vào Quiz, tạo quiz ôn tập theo topic, nộp kết quả.
8. Vào Phân tích học tập để xem dashboard cá nhân: tổng số câu hỏi, topic yếu, điểm quiz và gợi ý ôn tập.

## Đánh giá

Bộ câu hỏi đánh giá: `data/eval/eval_questions.csv` (50 câu, gồm 20 câu biên soạn tay + 30 câu tự sinh), gold chunk tương ứng tại `data/eval/gold_chunks.csv`.

Phương pháp và kết quả đánh giá thật (không phải số liệu minh họa) nằm tại `docs/evaluation_plan.md` và `reports/eval/`:
- Retrieval: HitRate@1/3/5/10, MRR@10, nDCG@10, latency — đo bằng `scripts/evaluate_retrieval.py` trên 6 cấu hình pipeline (A–F).
- Generation: Faithfulness và Answer Relevancy theo phương pháp claim-level (kiểu RAGAS) — đo bằng `scripts/evaluate_generation.py`.

Kết quả tiêu biểu (cấu hình C — Hybrid + Reranker, cấu hình mặc định của hệ thống): HitRate@3 = 87.5%, MRR@10 = 0.807, nDCG@10 = 0.828, latency trung bình ≈ 665 ms; Faithfulness trung bình 0.982 (n=43 câu có câu trả lời), Answer Relevancy trung bình 0.693 (n=43).

Bộ test tự động: `pytest tests/` — 70/70 test pass (routers auth/courses/documents/chat/quiz/dashboard/users, topic taxonomy).

## Ghi chú

- File `.env`, database local, vector store và dữ liệu processed được ignore khỏi Git.
- Nếu Gemini API hết quota, các endpoint dùng LLM (chat, quiz generate, taxonomy, recommendation) có thể trả lỗi 503/502, nhưng upload, index, retrieval search, profile, weak topic, quiz submit và dashboard vẫn kiểm tra độc lập được vì không phụ thuộc LLM.
