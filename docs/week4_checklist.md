# Checklist tuần 4

## Mục tiêu

- [x] Đánh giá thông số `chunk_size = 700`, `overlap = 100`, `top_k = 5`.
- [x] Viết hàm `split_text_with_overlap`.
- [x] Viết hàm `create_chunks`.
- [x] Gắn metadata cho từng chunk.
- [x] Giữ tương thích với hàm `chunk_text` cũ.
- [ ] Test chunking bằng Python trên file trong `data/processed`.
- [ ] Kết nối chunking với embedding service.
- [ ] Lưu chunk vào ChromaDB.
- [ ] Viết API retrieval.

## Ghi chú thông số

- `chunk_size = 700`: phù hợp để bắt đầu với tài liệu học tập tiếng Việt.
- `overlap = 100`: đủ để giảm rủi ro mất ngữ cảnh ở ranh giới chunk.
- `top_k = 5`: phù hợp cho bước retrieval demo ban đầu.

Các thông số này có thể điều chỉnh sau khi test trên tài liệu thật:

- Tăng `chunk_size` nếu câu trả lời thiếu ngữ cảnh.
- Giảm `top_k` nếu kết quả retrieval bị nhiễu.
- Tăng `overlap` nếu nội dung hay bị cắt giữa hai chunk.

