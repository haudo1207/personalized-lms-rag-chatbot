# Phạm vi đề tài

## Tên đề tài

Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation.

## Mục tiêu

Xây dựng hệ thống cho phép sinh viên upload tài liệu học tập và đặt câu hỏi. Hệ thống sử dụng RAG để tìm kiếm nội dung liên quan trong tài liệu, sau đó sinh câu trả lời có trích dẫn nguồn.

## Chức năng chính

- Upload tài liệu PDF/DOCX/TXT.
- Đọc và làm sạch nội dung tài liệu.
- Chia tài liệu thành các đoạn nhỏ.
- Tạo embedding và lưu vào vector database.
- Hỏi đáp dựa trên tài liệu.
- Trả lời có nguồn trích dẫn.
- Lưu lịch sử hỏi đáp.
- Cá nhân hóa nhẹ theo trình độ người học.
- Phát hiện topic yếu.
- Sinh quiz ôn tập.
- Gợi ý học tiếp.

## Không làm trong phiên bản 8 tuần

- Không tích hợp Moodle thật.
- Không làm mobile app.
- Không fine-tune model.
- Không làm multi-agent.
- Không làm dashboard giảng viên phức tạp.

## Môn học demo

Môn học demo: **Cơ sở dữ liệu**.

Các topic chính:

- Khóa chính.
- Khóa ngoại.
- SQL JOIN.
- Chuẩn hóa dữ liệu.
- ERD.
- 1NF, 2NF, 3NF.

## Flow demo cuối kỳ

Sinh viên chọn tài khoản -> upload tài liệu PDF/DOCX/TXT -> hệ thống đọc tài liệu -> chia chunk -> tạo embedding -> lưu vector database -> sinh viên hỏi câu hỏi -> chatbot trả lời dựa trên tài liệu -> hiển thị nguồn -> lưu lịch sử -> phát hiện topic yếu -> sinh quiz ôn tập -> gợi ý học tiếp.

