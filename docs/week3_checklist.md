# Checklist tuần 3

## Mục tiêu

- [x] Upload PDF/DOCX/TXT qua API.
- [x] Đọc nội dung PDF bằng PyMuPDF.
- [x] Đọc nội dung DOCX bằng python-docx.
- [x] Đọc nội dung TXT bằng UTF-8.
- [x] Làm sạch text cơ bản.
- [x] Lưu file raw vào `data/raw`.
- [x] Lưu text đã xử lý vào `data/processed`.
- [x] Lưu metadata document vào SQLite.
- [x] Giữ metadata số trang trong output processed text.
- [ ] Test Swagger trên máy có Python.

## API upload

```text
POST /documents/upload
```

Form fields:

```text
course_id = 1
user_id = 1
file = database_chapter_1.pdf
```

Kết quả mong đợi:

```json
{
  "message": "Document uploaded and processed",
  "document_id": 1,
  "file_name": "database_chapter_1.pdf",
  "status": "processed",
  "pages": 1,
  "processed_path": "data/processed/1_database_chapter_1.txt"
}
```

## Cách kiểm tra

```powershell
uvicorn backend.main:app --reload
```

Mở Swagger:

```text
http://127.0.0.1:8000/docs
```

Sau khi upload, kiểm tra:

- `data/raw`
- `data/processed`
- Nội dung file `.txt` trong `data/processed`

