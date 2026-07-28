# Báo cáo thực tập tuần 6

## NỘI DUNG THỰC HIỆN TRONG TUẦN

### Mô tả các nhiệm vụ đã thực hiện

- Xây dựng giao diện demo cho sinh viên bằng Streamlit tại `app/streamlit_app.py`.
- Thiết kế sidebar cho phép nhập `Backend API`, chọn `user_id`, `course_id` và số lượng nguồn truy xuất `top_k`.
- Xây dựng chức năng upload tài liệu PDF/DOCX/TXT từ giao diện.
- Kết nối giao diện upload với API `POST /documents/upload`.
- Xây dựng chức năng chọn tài liệu đã upload theo course hoặc nhập `Document ID` thủ công.
- Kết nối giao diện index tài liệu với API `POST /documents/{document_id}/index`.
- Xây dựng khu vực hỏi chatbot, gửi câu hỏi đến API `POST /chat/`.
- Hiển thị câu trả lời, nguồn tham khảo và thời gian phản hồi của chatbot.
- Xây dựng khu vực xem lịch sử hỏi đáp thông qua API `GET /chat/history/{user_id}`.
- Bổ sung xử lý lỗi rõ ràng khi backend chưa chạy, upload/index/chat thất bại hoặc LLM trả lỗi.
- Cập nhật `.gitignore` để bỏ qua thư mục `logs/` sinh ra khi chạy demo local.
- Kiểm tra backend FastAPI và Streamlit UI chạy được ở local.
- Commit và push mã nguồn tuần 6 lên GitHub.

### Những kiến thức/kỹ năng mới đã học được hoặc áp dụng

- Áp dụng Streamlit để xây dựng giao diện demo nhanh cho hệ thống AI/RAG.
- Biết cách gọi API FastAPI từ frontend Streamlit bằng thư viện `requests`.
- Biết cách gửi file upload từ UI sang backend dưới dạng multipart/form-data.
- Biết cách tổ chức giao diện theo luồng demo: upload tài liệu, index tài liệu, hỏi chatbot, xem nguồn và xem lịch sử.
- Hiểu hơn về cách quản lý trạng thái trong Streamlit bằng `st.session_state`.
- Biết cách hiển thị dữ liệu JSON, thông báo lỗi, loading spinner và lịch sử tương tác trong giao diện demo.
- Áp dụng kiểm thử khởi động cơ bản cho cả backend và frontend trước khi commit.

### Mức độ hoàn thành công việc theo mục tiêu đề ra

Mức độ tự đánh giá: **9/10**

Lý do:

- Đã hoàn thành giao diện demo đúng các chức năng chính của tuần 6.
- Giao diện có đủ upload tài liệu, index tài liệu, hỏi chatbot, xem nguồn và xem lịch sử hỏi đáp.
- Backend và Streamlit đều khởi động được.
- Chưa chấm 10/10 vì phần gọi chatbot thật vẫn phụ thuộc quota/API key Gemini từ tuần trước.

```text
Hoàn thành kém                                                Hoàn thành xuất sắc
1    2    3    4    5    6    7    8    [9]    10
```

### Khó khăn/vướng mắc gặp phải

- Cần đồng bộ đúng mã trạng thái HTTP giữa backend và UI. API upload trả `201 Created`, nếu UI chỉ kiểm tra `200 OK` thì sẽ báo lỗi giả.
- Giao diện cần xử lý trường hợp backend chưa chạy hoặc LLM lỗi quota để người dùng hiểu nguyên nhân.
- Streamlit rerun toàn bộ script sau mỗi tương tác, nên cần dùng `st.session_state` để giữ lại document ID, kết quả chat và lịch sử.
- Một số file cũ có lỗi hiển thị tiếng Việt do encoding, cần chú ý dùng UTF-8 khi chỉnh sửa.

### Cách xử lý hoặc hướng giải quyết

- Sửa UI để chấp nhận mọi response `2xx` là thành công thay vì chỉ kiểm tra `200`.
- Viết helper `request_json()` để gom logic gọi API và parse response.
- Viết helper `show_api_error()` để hiển thị lỗi HTTP/detail rõ ràng.
- Dùng `st.session_state` để giữ trạng thái sau khi upload, chat và xem lịch sử.
- Chạy `py_compile`, kiểm tra `/health` của FastAPI và kiểm tra Streamlit trả HTTP `200` trước khi commit.

### Phản hồi/Đánh giá từ người hướng dẫn (nếu có)

Chưa có phản hồi chính thức từ người hướng dẫn trong tuần này.

### Bạn cần GVHD hỗ trợ gì không

- Hỗ trợ góp ý bố cục giao diện demo sao cho phù hợp với yêu cầu bảo vệ.
- Xác nhận các minh chứng cần chụp cho phần giao diện: màn hình upload, index, hỏi chatbot, nguồn tham khảo và lịch sử hỏi đáp.
- Hỗ trợ định hướng cách trình bày hạn chế liên quan đến quota Gemini trong báo cáo.

### Cảm nhận chung về công việc đến thời điểm này

Mức độ cảm nhận: **4/5**

```text
1    2    3    [4]    5
```

Tuần này hệ thống đã có giao diện demo trực quan hơn, không còn chỉ kiểm thử qua Swagger. Việc có Streamlit giúp luồng sử dụng của sinh viên rõ ràng hơn: chọn user, chọn course, upload tài liệu, index và hỏi chatbot. Đây là bước quan trọng để sản phẩm gần với một hệ thống hoàn chỉnh hơn.

### Kế hoạch làm việc tiếp theo

- Bổ sung cá nhân hóa nhẹ cho chatbot.
- Phân loại topic câu hỏi của sinh viên.
- Lưu topic vào lịch sử hỏi đáp.
- Phát hiện topic yếu khi sinh viên hỏi lặp lại cùng một chủ đề.
- Điều chỉnh prompt theo trình độ beginner/advanced.
- Hiển thị thêm thông tin cá nhân hóa trên giao diện demo.

### Minh chứng công việc

Tên file minh chứng đề xuất:

```text
Tuần 6_Student_UI_HuuHau
```

### Mô tả minh chứng nộp

- Ảnh giao diện Streamlit.
- Ảnh sidebar chọn `user_id`, `course_id`.
- Ảnh upload tài liệu thành công.
- Ảnh index tài liệu thành công.
- Ảnh hỏi chatbot và hiển thị câu trả lời.
- Ảnh nguồn tham khảo của câu trả lời.
- Ảnh lịch sử hỏi đáp.
- Ảnh commit GitHub tuần 6.

