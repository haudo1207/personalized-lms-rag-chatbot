# Báo cáo thực tập tuần 4

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Nghiên cứu vai trò của chunking trong pipeline Retrieval-Augmented Generation.
- Đánh giá thông số chunk ban đầu cho tài liệu học tập tiếng Việt: `chunk_size = 700`, `overlap = 100`, `top_k = 5`.
- Xây dựng hàm chia văn bản có overlap để hạn chế mất ngữ cảnh giữa hai đoạn liên tiếp.
- Xây dựng hàm tạo chunk có metadata gồm `chunk_id`, `course_id`, `document_id`, `document_name`, `page`, `chunk_index` và `text`.
- Chuẩn bị nền tảng cho bước tiếp theo: tạo embedding, lưu vào ChromaDB và truy vấn retrieval.
- Cập nhật mã nguồn trong service `backend/services/chunking.py`.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Hiểu cách RAG chuyển tài liệu từ text thô thành các đoạn nhỏ có thể tìm kiếm ngữ nghĩa.
- Biết cách lựa chọn kích thước chunk và overlap phù hợp với tài liệu học tập.
- Áp dụng kỹ thuật gắn metadata cho chunk để phục vụ trích dẫn nguồn khi chatbot trả lời.
- Củng cố kỹ năng tổ chức service backend theo từng bước xử lý: upload, đọc file, làm sạch text, chunking.
- Áp dụng Git để quản lý thay đổi mã nguồn theo từng tuần thực tập.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **8/10**

Lý do:

- Đã hoàn thành chức năng chunking cốt lõi.
- Chunk đã có metadata cần thiết cho retrieval và hiển thị nguồn.
- Chưa kiểm thử runtime đầy đủ do môi trường máy chưa cài Python interpreter.

Thang đánh giá:

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    [8]    9    10
```

### Khó khăn/vướng mắc gặp phải

- Máy hiện tại chưa nhận Python interpreter nên chưa thể chạy trực tiếp `uvicorn`, test Swagger hoặc test script Python.
- Chưa có bước embedding và ChromaDB nên chunking mới dừng ở mức chuẩn bị dữ liệu đầu vào cho retrieval.
- Cần kiểm tra thêm chất lượng chunk trên tài liệu PDF/DOCX thật vì mỗi loại tài liệu có cách xuống dòng và định dạng khác nhau.

### Cách xử lý hoặc hướng giải quyết

- Tạm thời kiểm tra logic bằng cách rà soát mã nguồn và giữ hàm chunking đơn giản, dễ test.
- Thêm kiểm tra tham số để tránh lỗi lặp vô hạn khi `overlap >= chunk_size`.
- Sau khi cài Python và tạo `venv`, sẽ chạy test với tài liệu trong `data/processed`.
- Ở tuần tiếp theo, tiếp tục nối chunking với embedding service và ChromaDB.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong tuần này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ góp ý về kích thước chunk phù hợp với loại tài liệu môn học dùng để demo.
- Hỗ trợ xác nhận cách trình bày minh chứng cho pipeline RAG trong báo cáo thực tập.
- Nếu có thể, hỗ trợ cung cấp hoặc xác nhận bộ tài liệu PDF/DOCX mẫu phù hợp với môn Cơ sở dữ liệu.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Dự án đang đi đúng hướng theo lộ trình. Các phần nền tảng như cấu trúc backend, database, upload tài liệu, đọc và làm sạch text đã được xây dựng. Tuần này tiếp tục hoàn thiện bước chunking, là bước quan trọng để chuyển sang tìm kiếm ngữ nghĩa. Khó khăn chính hiện tại là môi trường chạy Python chưa sẵn sàng nên cần xử lý trước khi kiểm thử đầy đủ.

### Kế hoạch làm việc tiếp theo

- Cài Python, tạo môi trường `venv` và cài dependency từ `requirements.txt`.
- Chạy FastAPI và kiểm tra Swagger.
- Test upload tài liệu và kiểm tra file text sau xử lý.
- Test chunking trên file text trong `data/processed`.
- Xây dựng embedding service bằng sentence-transformers multilingual.
- Lưu chunk và embedding vào ChromaDB.
- Viết API retrieval để truy vấn các chunk liên quan theo câu hỏi.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 4_14-06_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh mã nguồn file `backend/services/chunking.py`.
- Ảnh cấu trúc thư mục project.
- Ảnh GitHub commit tuần 4.
- Ảnh file báo cáo thực tập tuần 4.
- Sau khi cài Python: ảnh terminal chạy API hoặc ảnh Swagger nếu kiểm thử được.

