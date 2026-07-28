# Nhật ký thực tập tuần 5 - Phần 1

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Tìm hiểu pipeline RAG chatbot theo luồng: câu hỏi -> retriever -> context -> prompt -> LLM -> câu trả lời kèm nguồn.
- Cài đặt Gemini SDK `google-generativeai` để chuẩn bị tích hợp mô hình ngôn ngữ.
- Cập nhật cấu hình đọc `GEMINI_API_KEY` và `GEMINI_MODEL` từ file `.env`.
- Viết service gọi LLM tại `backend/services/llm_service.py`.
- Kiểm tra danh sách model Gemini hỗ trợ `generateContent`.
- Phát hiện model `gemini-1.5-flash` trong kế hoạch ban đầu không còn dùng được với tài khoản/API hiện tại.
- Cập nhật model mặc định sang `gemini-2.0-flash`.
- Viết prompt RAG tại `backend/services/prompt_template.py`.
- Thiết kế prompt có quy tắc chỉ trả lời dựa trên tài liệu tham khảo, không bịa thông tin ngoài tài liệu.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Hiểu vai trò của LLM trong pipeline RAG: LLM không tự tìm tài liệu mà nhận context từ retriever.
- Biết cách cấu hình API key và model từ biến môi trường để tránh hard-code thông tin nhạy cảm.
- Biết cách kiểm tra model Gemini còn khả dụng bằng API thay vì chỉ dựa vào tên model trong kế hoạch.
- Biết cách viết prompt có ràng buộc nhằm hạn chế mô hình trả lời ngoài tài liệu.
- Hiểu tầm quan trọng của câu trả lời có nguồn trong hệ thống hỏi đáp tài liệu học tập.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **8/10**

Lý do:

- Đã hoàn thành cấu hình Gemini SDK.
- Đã viết LLM service.
- Đã viết prompt RAG.
- Đã phát hiện và xử lý vấn đề model cũ không còn khả dụng.
- Chưa sinh câu trả lời thật thành công vì API key hiện bị giới hạn quota.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    [8]    9    10
```

### Khó khăn/vướng mắc gặp phải

- Model `gemini-1.5-flash` trong kế hoạch ban đầu không còn xuất hiện trong danh sách model hỗ trợ `generateContent`.
- Package `google-generativeai` có cảnh báo deprecated và khuyến nghị chuyển sang package mới `google.genai`.
- Khi gọi model mới `gemini-2.0-flash`, API trả lỗi quota nên chưa kiểm thử được câu trả lời thật.

### Cách xử lý hoặc hướng giải quyết

- Dùng API để liệt kê danh sách model Gemini thật sự hỗ trợ `generateContent`.
- Đổi model mặc định từ `gemini-1.5-flash` sang `gemini-2.0-flash`.
- Giữ cấu hình model trong `.env.example` để dễ thay đổi về sau.
- Ghi chú rõ vấn đề quota trong checklist và báo cáo để không nhầm với lỗi code.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong phần công việc này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ xác nhận model Gemini nên dùng cho demo.
- Hỗ trợ góp ý cách trình bày lỗi quota/API trong báo cáo.
- Nếu có thể, hỗ trợ cung cấp API key có quota ổn định để test câu trả lời thật.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Phần tích hợp LLM giúp dự án tiến gần hơn đến sản phẩm chatbot hoàn chỉnh. Tuy có vướng mắc ở API quota, phần thiết kế prompt và cấu hình service đã rõ ràng, có thể tiếp tục mở rộng khi có API key hoạt động ổn định.

### Kế hoạch làm việc tiếp theo

- Hoàn thiện RAG pipeline nối retriever, prompt và LLM.
- Xây dựng Chat API để người dùng gửi câu hỏi.
- Lưu lịch sử hỏi đáp vào database.
- Test câu hỏi có trong tài liệu, câu hỏi so sánh và câu hỏi ngoài tài liệu.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 5_Phần 1_27-06_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh mã nguồn `backend/services/llm_service.py`.
- Ảnh mã nguồn `backend/services/prompt_template.py`.
- Ảnh cấu hình `.env.example`.
- Ảnh lỗi quota hoặc ghi chú model Gemini đã kiểm tra.

