# RAG Learning Chatbot

Hệ thống chatbot hỏi đáp tài liệu học tập cho sinh viên sử dụng Retrieval-Augmented Generation (RAG), có hỗ trợ cá nhân hóa nhẹ, phát hiện topic yếu, tạo quiz ôn tập và dashboard học tập đơn giản.

## Tên đề tài

**Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation.**

## Chức năng chính

- Quản lý user và course.
- Upload tài liệu PDF/DOCX/TXT.
- Đọc, làm sạch và lưu nội dung tài liệu đã xử lý.
- Chia tài liệu thành chunk có overlap.
- Tạo embedding bằng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Lưu vector và metadata vào ChromaDB.
- Truy xuất đoạn tài liệu liên quan theo câu hỏi.
- Gọi Gemini API để trả lời dựa trên context RAG.
- Trả lời kèm nguồn tham khảo và latency.
- Lưu lịch sử hỏi đáp.
- Phân loại topic câu hỏi.
- Phát hiện weak topic khi sinh viên hỏi cùng topic nhiều lần.
- Cá nhân hóa prompt theo level beginner/advanced, recent questions và weak topics.
- Tạo quiz ôn tập từ tài liệu.
- Lưu kết quả quiz.
- Gợi ý ôn tập dựa trên weak topics.
- Dashboard sinh viên đơn giản.

## Công nghệ sử dụng

- Python
- FastAPI
- Streamlit
- SQLite
- ChromaDB
- Sentence Transformers
- Gemini API
- PyMuPDF
- python-docx
- SQLAlchemy
- Git/GitHub

## Cấu trúc thư mục

```text
backend/
  models/          SQLAlchemy models
  routers/         FastAPI routers
  services/        RAG, embedding, quiz, personalization services
app/
  streamlit_app.py Streamlit demo UI
data/
  raw/             Tài liệu gốc
  processed/       Tài liệu đã xử lý
  eval/            Bộ câu hỏi đánh giá
docs/              Tài liệu kiến trúc, kế hoạch, đánh giá
reports/           Báo cáo và minh chứng
vector_store/      ChromaDB local
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
GEMINI_MODEL=gemini-2.0-flash
```

## Chạy backend

```powershell
uvicorn backend.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Chạy giao diện Streamlit

```powershell
streamlit run app/streamlit_app.py
```

URL mặc định:

```text
http://127.0.0.1:8501
```

## API chính

### Documents

- `POST /documents/upload`: upload và xử lý tài liệu.
- `POST /documents/{document_id}/index`: tạo chunk, embedding và lưu vào ChromaDB.
- `GET /documents/`: danh sách tài liệu.

### Retrieval

- `POST /retrieval/search`: tìm các chunk liên quan đến câu hỏi.

### Chat

- `POST /chat/`: hỏi chatbot RAG cá nhân hóa.
- `GET /chat/history/{user_id}`: xem lịch sử hỏi đáp.
- `GET /chat/profile/{user_id}/{course_id}`: xem user profile.
- `GET /chat/weak-topics/{user_id}/{course_id}`: xem topic yếu.

### Quiz

- `POST /quiz/generate`: sinh quiz từ tài liệu.
- `POST /quiz/submit`: lưu kết quả quiz.
- `GET /quiz/results/{user_id}`: xem kết quả quiz.

### Dashboard

- `GET /dashboard/student/{user_id}?course_id=1`: dashboard học tập cá nhân.

## Demo flow

1. Chạy FastAPI backend.
2. Chạy Streamlit UI.
3. Chọn `user_id` và `course_id`.
4. Upload tài liệu học tập.
5. Index tài liệu.
6. Hỏi chatbot, kiểm tra câu trả lời và nguồn.
7. Hỏi cùng một topic từ 3 lần để phát hiện weak topic.
8. Tạo quiz ôn tập theo topic.
9. Nộp kết quả quiz.
10. Xem dashboard cá nhân gồm tổng số câu hỏi, topic yếu, điểm quiz và gợi ý ôn tập.

## Đánh giá

Bộ câu hỏi đánh giá nằm tại:

```text
data/eval/eval_questions.csv
```

Tiêu chí đánh giá và bảng so sánh mẫu nằm tại:

```text
docs/evaluation_plan.md
```

Các tiêu chí gồm Accuracy, Faithfulness, Relevance, Citation và Hallucination.

## Ghi chú

- File `.env`, database local, vector store và dữ liệu processed được ignore khỏi Git.
- Nếu Gemini API hết quota, các endpoint dùng LLM có thể trả lỗi quota, nhưng các phần upload, index, retrieval, profile, weak topic, quiz submit và dashboard vẫn có thể kiểm tra độc lập.
