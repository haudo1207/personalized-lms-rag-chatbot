# Checklist tuần 4

## Mục tiêu

- [x] Đánh giá thông số `chunk_size = 700`, `overlap = 100`, `top_k = 5`.
- [x] Viết hàm `split_text_with_overlap`.
- [x] Viết hàm `create_chunks`.
- [x] Gắn metadata cho từng chunk.
- [x] Giữ tương thích với hàm `chunk_text` cũ.
- [x] Test chunking bằng Python trên tài liệu upload mẫu.
- [x] Kết nối chunking với embedding service.
- [x] Lưu chunk vào ChromaDB.
- [x] Viết API retrieval.
- [x] Test flow upload -> index -> retrieval.

## Ghi chú thông số

- `chunk_size = 700`: phù hợp để bắt đầu với tài liệu học tập tiếng Việt.
- `overlap = 100`: đủ để giảm rủi ro mất ngữ cảnh ở ranh giới chunk.
- `top_k = 5`: phù hợp cho bước retrieval demo ban đầu.

Các thông số này có thể điều chỉnh sau khi test trên tài liệu thật:

- Tăng `chunk_size` nếu câu trả lời thiếu ngữ cảnh.
- Giảm `top_k` nếu kết quả retrieval bị nhiễu.
- Tăng `overlap` nếu nội dung hay bị cắt giữa hai chunk.

## Kết quả test

Flow đã kiểm tra:

1. Tạo user test.
2. Tạo course test.
3. Upload file TXT mẫu.
4. Index document vào ChromaDB.
5. Gọi `POST /retrieval/search` với câu hỏi: `Khoa chinh la gi?`.

Kết quả:

- API upload trả `201`.
- API index trả `200`.
- API retrieval trả `200`.
- Retrieval trả về chunk liên quan đến khóa chính.
- Kết quả có `document_name`, `page`, `distance`.

Đánh giá hiện tại: pipeline retrieval đã đạt hiệu quả ở mức demo cơ bản. Cần test thêm với PDF/DOCX tiếng Việt thật để đánh giá độ sạch text, độ nhiễu chunk và chất lượng ranking.
