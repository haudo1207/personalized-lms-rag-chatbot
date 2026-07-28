# Nhật ký thực tập tuần 5 - Phần 2

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Viết RAG pipeline tại `backend/services/rag_pipeline.py`.
- Xây dựng hàm lấy các chunk liên quan từ retriever.
- Định dạng context từ chunk, có gắn nguồn theo dạng tên tài liệu và số trang.
- Gọi prompt RAG và LLM service để tạo câu trả lời.
- Trả về kết quả gồm `answer`, `sources` và `latency`.
- Viết Chat API tại `backend/routers/chat.py` với endpoint `POST /chat/`.
- Lưu lịch sử hỏi đáp vào bảng `chat_history`.
- Viết API xem lịch sử chat theo user: `GET /chat/history/{user_id}`.
- Test Chat API bằng mock LLM để kiểm tra pipeline hoạt động không phụ thuộc quota Gemini.
- Kiểm tra API xử lý lỗi Gemini quota rõ ràng, trả lỗi thay vì làm backend crash.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Biết cách ghép retriever, context, prompt và LLM thành pipeline RAG hoàn chỉnh.
- Biết cách trả về nguồn trích dẫn để người học kiểm chứng câu trả lời.
- Áp dụng FastAPI để xây dựng API hỏi đáp.
- Áp dụng SQLAlchemy để lưu lịch sử chat vào database.
- Biết cách đo latency cho mỗi câu hỏi.
- Biết cách dùng mock LLM để test logic backend khi API thật bị giới hạn quota.
- Biết cách xử lý lỗi từ dịch vụ bên ngoài để backend không bị crash.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **8/10**

Lý do:

- RAG pipeline đã được xây dựng.
- Chat API đã hoạt động.
- Có sources và latency.
- Có lưu chat history.
- Test bằng mock LLM đã pass.
- Chưa test được câu trả lời Gemini thật do quota API hiện tại bằng `0`.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    [8]    9    10
```

### Khó khăn/vướng mắc gặp phải

- Gemini API trả lỗi `429 ResourceExhausted`, quota free tier hiện tại bằng `0`.
- Vì lỗi quota, chưa thể chụp minh chứng câu trả lời thật từ Gemini trên Swagger.
- Một số output tiếng Việt trong terminal bị lỗi hiển thị encoding khi chạy script qua PowerShell.

### Cách xử lý hoặc hướng giải quyết

- Test Chat API bằng mock LLM để xác nhận logic RAG, sources, latency và lưu lịch sử hoạt động đúng.
- Bổ sung xử lý lỗi trong Chat API để khi Gemini lỗi quota/API, backend trả thông báo rõ ràng.
- Ghi chú vấn đề quota trong checklist tuần 5.
- Khi có API key/quota khả dụng, sẽ test lại các câu hỏi:
  - `Khóa chính là gì?`
  - `INNER JOIN khác LEFT JOIN như thế nào?`
  - `Ai là tổng thống Mỹ hiện tại?`

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong phần công việc này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ xác nhận có thể dùng mock LLM làm minh chứng tạm thời khi API bị quota hay không.
- Hỗ trợ cung cấp API key có quota để test câu trả lời thật.
- Hỗ trợ góp ý tiêu chí đánh giá chất lượng câu trả lời RAG.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Tuần này là bước chuyển quan trọng từ hệ thống truy xuất tài liệu sang chatbot hỏi đáp. Phần backend đã có đủ các thành phần chính: retrieval, prompt, LLM service, Chat API và chat history. Dù còn vướng quota Gemini, cấu trúc hệ thống đã sẵn sàng để demo khi có API key hoạt động.

### Kế hoạch làm việc tiếp theo

- Chuẩn bị API key Gemini có quota hoặc bật billing.
- Test lại Chat API với LLM thật.
- Chụp minh chứng Swagger câu trả lời có nguồn.
- Chụp minh chứng câu hỏi ngoài tài liệu bị từ chối.
- Chụp minh chứng bảng `chat_history`.
- Cải thiện frontend Streamlit để hỏi đáp trực tiếp thay vì chỉ test qua Swagger.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 5_Phần 2_27-06_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh mã nguồn `backend/services/rag_pipeline.py`.
- Ảnh mã nguồn `backend/routers/chat.py`.
- Ảnh endpoint `POST /chat/` trên Swagger.
- Ảnh bảng `chat_history`.
- Ảnh lỗi quota Gemini hoặc kết quả test mock LLM.

