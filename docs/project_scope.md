# Phạm vi đề tài

## Tên đề tài

Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation.

## Mục tiêu

Xây dựng hệ thống cho phép sinh viên upload tài liệu học tập và đặt câu hỏi. Hệ thống sử dụng RAG để tìm kiếm nội dung liên quan trong tài liệu, sau đó sinh câu trả lời có trích dẫn nguồn.

## Chức năng chính

- Đăng nhập bằng JWT; mô hình course theo quyền sở hữu (mỗi course thuộc một sinh viên, không có bước enroll).
- Upload tài liệu PDF/DOCX/TXT.
- Đọc và làm sạch nội dung tài liệu.
- Chia tài liệu thành các đoạn nhỏ theo ngữ nghĩa (semantic chunking).
- Tạo embedding và lưu vào vector database.
- Hỏi đáp dựa trên tài liệu, truy xuất Hybrid (Dense + BM25 + RRF) và re-rank bằng Cross-Encoder.
- Trả lời có nguồn trích dẫn.
- Lưu lịch sử hỏi đáp.
- Cá nhân hóa nhẹ theo trình độ người học.
- Phát hiện topic yếu.
- Sinh quiz ôn tập, độ khó tự thích ứng theo điểm quiz gần nhất.
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

Sinh viên đăng nhập (JWT) -> chọn/tạo course -> upload tài liệu PDF/DOCX/TXT -> hệ thống đọc tài liệu -> chia chunk -> tạo embedding -> lưu vector database -> sinh viên hỏi câu hỏi -> chatbot truy xuất Hybrid + rerank rồi trả lời dựa trên tài liệu -> hiển thị nguồn -> lưu lịch sử -> phát hiện topic yếu -> sinh quiz ôn tập -> gợi ý học tiếp.

