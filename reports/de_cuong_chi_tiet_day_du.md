# ĐỀ CƯƠNG CHI TIẾT BÁO CÁO

Tên đề tài: **Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation**

## MỤC LỤC

1. Thông tin chung về đề tài
2. Mục tiêu và phạm vi thực hiện
3. Đề cương chi tiết các chương
4. Kế hoạch thực hiện
5. Sản phẩm dự kiến
6. Nội dung Chương 1. Tổng quan đề tài

## 1. Thông tin chung về đề tài

Đề tài tập trung xây dựng một hệ thống chatbot hỗ trợ sinh viên hỏi đáp dựa trên tài liệu học tập đã upload. Hệ thống sử dụng kỹ thuật Retrieval-Augmented Generation (RAG) để truy xuất các đoạn tài liệu liên quan, sau đó dùng mô hình ngôn ngữ lớn để tạo câu trả lời có nguồn trích dẫn.

Phiên bản demo của hệ thống được định hướng phục vụ môn Cơ sở dữ liệu, với các chủ đề thường gặp như khóa chính, khóa ngoại, SQL JOIN, chuẩn hóa dữ liệu, ERD, 1NF, 2NF và 3NF.

## 2. Mục tiêu và phạm vi thực hiện

### 2.1. Mục tiêu tổng quát

Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập cho sinh viên, cho phép upload tài liệu, xử lý nội dung, tìm kiếm ngữ nghĩa và trả lời câu hỏi dựa trên tài liệu tham khảo.

### 2.2. Mục tiêu cụ thể

- Xây dựng backend API bằng FastAPI.
- Xây dựng cơ sở dữ liệu SQLite lưu người dùng, khóa học, tài liệu và lịch sử hỏi đáp.
- Hỗ trợ upload tài liệu PDF, DOCX và TXT.
- Đọc, làm sạch và chia nhỏ tài liệu thành các chunk.
- Tạo embedding bằng mô hình sentence-transformers đa ngôn ngữ.
- Lưu vector embedding vào ChromaDB.
- Xây dựng chức năng retrieval để tìm các đoạn tài liệu liên quan.
- Tích hợp Gemini API để sinh câu trả lời.
- Trả lời câu hỏi kèm nguồn trích dẫn.
- Lưu lịch sử hỏi đáp phục vụ các chức năng cá nhân hóa về sau.

### 2.3. Phạm vi thực hiện

Trong giai đoạn thực tập, hệ thống tập trung vào phiên bản demo chạy local. Các chức năng chính gồm upload tài liệu, xử lý tài liệu, tạo embedding, lưu vector, retrieval, hỏi đáp RAG và lưu lịch sử chat.

Các chức năng chưa thực hiện trong phạm vi hiện tại gồm tích hợp Moodle thật, xây dựng mobile app, fine-tune mô hình ngôn ngữ, triển khai hệ thống cloud hoàn chỉnh và dashboard giảng viên nâng cao.

## 3. Đề cương chi tiết các chương

### Chương 1. Tổng quan đề tài

1.1. Lý do chọn đề tài  
1.2. Mục tiêu đề tài  
1.3. Đối tượng và phạm vi nghiên cứu  
1.4. Bài toán cần giải quyết  
1.5. Phương pháp thực hiện  
1.6. Công nghệ sử dụng  
1.7. Kết quả dự kiến đạt được  
1.8. Bố cục báo cáo

### Chương 2. Cơ sở lý thuyết

2.1. Tổng quan về chatbot  
2.2. Tổng quan về mô hình ngôn ngữ lớn  
2.3. Retrieval-Augmented Generation  
2.4. Embedding và tìm kiếm ngữ nghĩa  
2.5. Vector database và ChromaDB  
2.6. Xử lý tài liệu PDF, DOCX, TXT  
2.7. FastAPI và REST API  
2.8. Streamlit và giao diện demo  
2.9. Cá nhân hóa học tập  
2.10. Phát hiện topic yếu và sinh quiz ôn tập

### Chương 3. Phân tích và thiết kế hệ thống

3.1. Khảo sát bài toán và nhu cầu người dùng  
3.2. Yêu cầu chức năng  
3.3. Yêu cầu phi chức năng  
3.4. Kiến trúc tổng thể hệ thống  
3.5. Thiết kế luồng upload và xử lý tài liệu  
3.6. Thiết kế luồng index tài liệu vào vector database  
3.7. Thiết kế luồng retrieval  
3.8. Thiết kế luồng chatbot RAG  
3.9. Thiết kế cơ sở dữ liệu quan hệ  
3.10. Thiết kế API backend  
3.11. Thiết kế giao diện demo

### Chương 4. Xây dựng hệ thống

4.1. Xây dựng cấu trúc project  
4.2. Xây dựng backend FastAPI  
4.3. Xây dựng database SQLite  
4.4. Xây dựng chức năng quản lý user và course  
4.5. Xây dựng chức năng upload tài liệu  
4.6. Xử lý đọc file PDF, DOCX, TXT  
4.7. Làm sạch văn bản  
4.8. Chia tài liệu thành chunks  
4.9. Tạo embedding bằng multilingual Sentence Transformers  
4.10. Lưu embedding vào ChromaDB  
4.11. Xây dựng retrieval service  
4.12. Xây dựng prompt RAG  
4.13. Tích hợp Gemini API  
4.14. Xây dựng Chat API  
4.15. Lưu lịch sử hỏi đáp  
4.16. Xây dựng giao diện demo bằng Streamlit

### Chương 5. Kiểm thử và đánh giá

5.1. Môi trường kiểm thử  
5.2. Dữ liệu kiểm thử  
5.3. Kiểm thử upload tài liệu  
5.4. Kiểm thử đọc và làm sạch tài liệu  
5.5. Kiểm thử chunking  
5.6. Kiểm thử embedding và lưu ChromaDB  
5.7. Kiểm thử retrieval  
5.8. Kiểm thử Chat API  
5.9. Kiểm thử lưu lịch sử hỏi đáp  
5.10. Đánh giá kết quả đạt được  
5.11. Hạn chế của hệ thống

### Chương 6. Kết luận và hướng phát triển

6.1. Kết quả đạt được  
6.2. Những hạn chế còn tồn tại  
6.3. Bài học kinh nghiệm  
6.4. Hướng phát triển trong tương lai

## 4. Kế hoạch thực hiện

- Tuần 1: Chốt đề tài, phạm vi, cấu trúc project, README và tài liệu kiến trúc.
- Tuần 2: Xây dựng backend FastAPI và database cơ bản.
- Tuần 3: Xây dựng chức năng upload, đọc và làm sạch tài liệu.
- Tuần 4: Xây dựng chunking, embedding, ChromaDB và retrieval.
- Tuần 5: Xây dựng RAG chatbot trả lời có nguồn và lưu chat history.
- Tuần 6: Hoàn thiện giao diện demo và cải thiện trải nghiệm người dùng.
- Tuần 7: Kiểm thử, đánh giá chất lượng câu trả lời và hoàn thiện minh chứng.
- Tuần 8: Hoàn thiện báo cáo, slide và chuẩn bị demo.

## 5. Sản phẩm dự kiến

- Source code hệ thống được quản lý trên GitHub.
- Backend API chạy được bằng FastAPI.
- Database SQLite có các bảng người dùng, khóa học, tài liệu và lịch sử hỏi đáp.
- Chức năng upload và xử lý tài liệu PDF, DOCX, TXT.
- Chức năng chunking, embedding và lưu vector vào ChromaDB.
- Chức năng retrieval tìm các đoạn liên quan.
- Chat API trả lời dựa trên tài liệu và có nguồn.
- Giao diện demo bằng Streamlit.
- Báo cáo thực tập và minh chứng theo từng tuần.
