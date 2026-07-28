# Báo cáo thực tập tuần 5

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Xây dựng pipeline RAG chatbot theo luồng: câu hỏi -> retriever -> context -> prompt -> LLM -> câu trả lời kèm nguồn.
- Cài đặt Gemini SDK `google-generativeai` để chuẩn bị gọi mô hình ngôn ngữ.
- Cập nhật cấu hình đọc `GEMINI_API_KEY` và `GEMINI_MODEL` từ file `.env`.
- Viết service gọi LLM tại `backend/services/llm_service.py`.
- Viết prompt RAG tại `backend/services/prompt_template.py` với quy tắc chỉ trả lời dựa trên tài liệu tham khảo, không bịa thông tin ngoài tài liệu.
- Viết RAG pipeline tại `backend/services/rag_pipeline.py`, gồm truy xuất chunk liên quan, tạo context, build prompt, gọi LLM, trả về answer, sources và latency.
- Viết Chat API tại `backend/routers/chat.py` với endpoint `POST /chat/`.
- Lưu lịch sử hỏi đáp vào bảng `chat_history`.
- Viết API xem lịch sử chat theo user: `GET /chat/history/{user_id}`.
- Kiểm thử Chat API bằng mock LLM để xác nhận pipeline, sources, latency và lưu lịch sử hoạt động đúng.
- Kiểm tra Gemini API thật và phát hiện model `gemini-1.5-flash` không còn dùng được trong tài khoản/API hiện tại; chuyển default sang `gemini-2.0-flash`.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Hiểu cách ghép các thành phần retrieval, prompt và LLM thành một pipeline RAG hoàn chỉnh.
- Biết cách xây dựng prompt có ràng buộc để hạn chế mô hình trả lời ngoài tài liệu.
- Biết cách định dạng context từ các chunk có metadata nguồn, gồm tên tài liệu và số trang.
- Áp dụng FastAPI để xây dựng Chat API nhận câu hỏi và trả về câu trả lời có nguồn.
- Áp dụng SQLAlchemy để lưu lịch sử hỏi đáp vào database.
- Biết cách xử lý lỗi khi gọi LLM, ví dụ thiếu API key, model không hỗ trợ hoặc hết quota.
- Hiểu thêm về giới hạn thực tế của API bên ngoài: model có thể thay đổi và tài khoản có thể bị giới hạn quota.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **8/10**

Lý do:

- Đã hoàn thành phần code chính của RAG chatbot.
- Chat API đã chạy được với mock LLM.
- Có sources, latency và lưu chat history.
- Đã kiểm tra được kết nối Gemini API thật, nhưng chưa sinh câu trả lời thật thành công do quota tài khoản Gemini hiện tại bằng `0`.

Thang đánh giá:

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    [8]    9    10
```

### Khó khăn/vướng mắc gặp phải

- Model `gemini-1.5-flash` trong kế hoạch ban đầu không còn xuất hiện trong danh sách model hỗ trợ `generateContent` của tài khoản/API hiện tại.
- Sau khi đổi sang `gemini-2.0-flash`, API trả lỗi `429 ResourceExhausted` do quota free tier hiện tại bằng `0`.
- Package `google-generativeai` có cảnh báo deprecated và khuyến nghị chuyển sang package mới `google.genai`.
- Khi test trong PowerShell, một số output tiếng Việt bị lỗi hiển thị encoding, dù dữ liệu xử lý chính vẫn dùng UTF-8.

### Cách xử lý hoặc hướng giải quyết

- Dùng `genai.list_models()` để kiểm tra danh sách model thật sự hỗ trợ `generateContent`.
- Đổi model mặc định từ `gemini-1.5-flash` sang `gemini-2.0-flash`.
- Bổ sung xử lý lỗi trong Chat API để khi LLM lỗi quota/API, backend trả lỗi rõ ràng thay vì crash.
- Test pipeline bằng mock LLM để xác nhận phần retrieval, prompt, Chat API và lưu `chat_history` hoạt động đúng.
- Ở bước tiếp theo cần dùng API key Gemini còn quota, bật billing hoặc chuyển sang provider/model khác nếu cần demo ngay.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong tuần này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ xác nhận yêu cầu demo có bắt buộc gọi LLM online thật hay có thể minh chứng bằng mock LLM trong trường hợp API bị giới hạn quota.
- Hỗ trợ góp ý cách trình bày phần lỗi quota Gemini trong báo cáo.
- Nếu có thể, hỗ trợ cung cấp tài khoản/API key có quota ổn định để demo chức năng hỏi đáp thật.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Dự án đã đi đến phần quan trọng nhất: chatbot có thể nhận câu hỏi, lấy ngữ cảnh từ tài liệu, tạo prompt, gọi LLM và lưu lịch sử hỏi đáp. Phần code nền tảng đã tương đối rõ ràng và có thể mở rộng tiếp. Khó khăn lớn nhất hiện tại không nằm ở logic hệ thống mà nằm ở điều kiện sử dụng API Gemini thật. Nhìn chung tiến độ vẫn tốt, nhưng cần xử lý quota/API key để demo tuần sau mượt hơn.

### Kế hoạch làm việc tiếp theo

- Chuẩn bị API key Gemini có quota hoặc cấu hình billing phù hợp.
- Test lại `POST /chat/` bằng LLM thật.
- Chụp minh chứng Swagger cho câu hỏi có trong tài liệu.
- Chụp minh chứng câu trả lời có nguồn.
- Test câu hỏi ngoài tài liệu và kiểm tra hệ thống từ chối trả lời.
- Chụp minh chứng bảng `chat_history` trong database.
- Cải thiện frontend Streamlit để sinh viên có thể hỏi đáp trực tiếp thay vì chỉ test qua Swagger.
- Bổ sung đánh giá chất lượng câu trả lời theo các nhóm câu hỏi: định nghĩa, so sánh, câu ngoài tài liệu.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 5_26-06_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh mã nguồn `backend/services/llm_service.py`.
- Ảnh mã nguồn `backend/services/prompt_template.py`.
- Ảnh mã nguồn `backend/services/rag_pipeline.py`.
- Ảnh mã nguồn `backend/routers/chat.py`.
- Ảnh commit GitHub tuần 5.
- Ảnh Swagger endpoint `POST /chat/`.
- Ảnh database có bảng `chat_history`.
- Ghi chú minh chứng lỗi Gemini quota nếu chưa có API key/quota khả dụng.

