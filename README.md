# RAG Learning Chatbot

## 1. Giới thiệu

Hệ thống chatbot hỏi đáp tài liệu học tập cho sinh viên sử dụng Retrieval-Augmented Generation.

Tên đề tài:

**Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation.**

## 2. Mục tiêu

- Cho phép sinh viên upload tài liệu PDF/DOCX/TXT.
- Hỏi đáp dựa trên nội dung tài liệu đã upload.
- Trả lời có nguồn trích dẫn.
- Lưu lịch sử học tập.
- Cá nhân hóa phản hồi theo trình độ người học.
- Phát hiện topic yếu.
- Sinh quiz ôn tập từ tài liệu.
- Gợi ý nội dung học tiếp.

## 3. Công nghệ sử dụng

- Python
- FastAPI
- Streamlit
- SQLite
- ChromaDB
- Sentence Transformers
- Gemini API
- PyMuPDF
- python-docx
- pandas

## 4. Cấu trúc thư mục

```text
backend/        FastAPI backend, models, routers, services
app/            Streamlit demo frontend
data/raw/       Tài liệu học tập gốc
data/processed/ Dữ liệu đã xử lý
data/eval/      Bộ câu hỏi và kết quả đánh giá
vector_store/   Dữ liệu ChromaDB local
experiments/    Thử nghiệm và notebook/script phụ
reports/        Tài liệu báo cáo
docs/           Phạm vi, kiến trúc, kế hoạch
```

## 5. Cách chạy

Tạo môi trường Python:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Chạy backend:

```powershell
uvicorn backend.main:app --reload
```

Chạy frontend demo:

```powershell
streamlit run app/streamlit_app.py
```

## 6. Trạng thái tuần 1

- [x] Có cấu trúc thư mục.
- [x] Có README.
- [x] Có `.env.example`.
- [x] Có `.gitignore`.
- [x] Có `docs/project_scope.md`.
- [x] Có `docs/architecture.md`.
- [x] Có tài liệu mẫu trong `data/raw/`.
- [ ] Có repo GitHub remote.

