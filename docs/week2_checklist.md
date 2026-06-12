# Checklist tuần 2

## Mục tiêu

- [x] FastAPI app chạy được.
- [x] Có endpoint `/` và `/health`.
- [x] Có cấu hình database SQLite.
- [x] Có bảng `users`.
- [x] Có bảng `courses`.
- [x] Có bảng `documents`.
- [x] Có bảng `chat_history`.
- [x] Có API tạo user.
- [x] Có API lấy danh sách user.
- [x] Có API tạo course.
- [x] Có API lấy danh sách course.
- [ ] Kiểm tra Swagger tại `http://127.0.0.1:8000/docs` trên máy có Python.

## Dữ liệu test Swagger

### User mẫu

```json
{
  "full_name": "Nguyen Van A",
  "email": "a@student.edu.vn",
  "role": "student",
  "level": "beginner"
}
```

### Course mẫu

```json
{
  "course_code": "DB101",
  "course_name": "Co so du lieu",
  "description": "Mon hoc ve SQL, khoa chinh, khoa ngoai va chuan hoa CSDL."
}
```

## Cách chạy

```powershell
uvicorn backend.main:app --reload
```

Mở Swagger:

```text
http://127.0.0.1:8000/docs
```

