# CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI

Tên đề tài: **Xây dựng hệ thống chatbot hỏi đáp tài liệu học tập có hỗ trợ cá nhân hóa cho sinh viên sử dụng Retrieval-Augmented Generation.**

## 1.1. Lý do chọn đề tài

Trong bối cảnh chuyển đổi số giáo dục, sinh viên ngày càng tiếp cận nhiều tài liệu học tập ở nhiều định dạng khác nhau như PDF, DOCX, TXT, slide bài giảng, giáo trình và tài liệu tham khảo. Khối lượng tài liệu lớn giúp người học có nhiều nguồn thông tin hơn, nhưng đồng thời cũng làm tăng khó khăn trong việc tìm kiếm nhanh nội dung cần thiết. Khi cần ôn tập hoặc giải đáp một khái niệm cụ thể, sinh viên thường phải đọc lại nhiều trang tài liệu, tìm kiếm thủ công hoặc phụ thuộc vào các công cụ tìm kiếm chung không bám sát nội dung môn học.

Các chatbot sử dụng mô hình ngôn ngữ lớn có khả năng trả lời tự nhiên, dễ hiểu và hỗ trợ người học tương tác thuận tiện hơn. Tuy nhiên, nếu chỉ sử dụng mô hình ngôn ngữ thông thường, hệ thống có thể trả lời dựa trên tri thức tổng quát thay vì dựa trên tài liệu học tập cụ thể. Điều này làm phát sinh rủi ro trả lời sai, trả lời thiếu nguồn hoặc bịa thông tin không có trong tài liệu.

Retrieval-Augmented Generation (RAG) là hướng tiếp cận phù hợp để giải quyết vấn đề trên. RAG kết hợp tìm kiếm nội dung liên quan trong tài liệu với khả năng sinh câu trả lời của mô hình ngôn ngữ. Nhờ đó, chatbot có thể trả lời dựa trên tài liệu đã upload, đồng thời hiển thị nguồn tham khảo như tên tài liệu và số trang. Vì vậy, đề tài này được lựa chọn nhằm xây dựng một hệ thống chatbot học tập có tính ứng dụng thực tế, phù hợp với nhu cầu tra cứu, ôn tập và hỗ trợ cá nhân hóa cho sinh viên.

## 1.2. Mục tiêu đề tài

Mục tiêu tổng quát của đề tài là xây dựng hệ thống chatbot hỗ trợ sinh viên hỏi đáp dựa trên tài liệu học tập đã cung cấp. Hệ thống sử dụng kỹ thuật Retrieval-Augmented Generation để tìm kiếm nội dung liên quan trong tài liệu, sau đó dùng mô hình ngôn ngữ để tạo câu trả lời rõ ràng, dễ hiểu và có nguồn trích dẫn.

Các mục tiêu cụ thể gồm: xây dựng backend API bằng FastAPI; xây dựng cơ sở dữ liệu lưu thông tin người dùng, khóa học, tài liệu và lịch sử hỏi đáp; hỗ trợ upload tài liệu PDF, DOCX, TXT; đọc và làm sạch nội dung tài liệu; chia tài liệu thành các đoạn nhỏ; tạo embedding bằng mô hình sentence-transformers đa ngôn ngữ; lưu vector vào ChromaDB; xây dựng chức năng retrieval; tích hợp Gemini API để sinh câu trả lời; trả lời kèm nguồn; và lưu lịch sử hỏi đáp phục vụ các bước cá nhân hóa về sau.

## 1.3. Đối tượng và phạm vi nghiên cứu

Đối tượng nghiên cứu của đề tài là quy trình xây dựng hệ thống chatbot hỏi đáp tài liệu học tập dựa trên RAG. Trong đó, trọng tâm gồm xử lý tài liệu, tạo embedding, lưu trữ vector, truy xuất nội dung liên quan và sinh câu trả lời dựa trên ngữ cảnh tài liệu.

Đối tượng sử dụng dự kiến là sinh viên có nhu cầu tra cứu, ôn tập và đặt câu hỏi về tài liệu môn học. Trong phiên bản demo, đề tài tập trung vào môn Cơ sở dữ liệu với các chủ đề như khóa chính, khóa ngoại, SQL JOIN, chuẩn hóa dữ liệu, ERD, 1NF, 2NF và 3NF.

Phạm vi thực hiện trong giai đoạn thực tập tập trung vào hệ thống chạy local, có backend FastAPI, database SQLite, vector database ChromaDB và giao diện demo Streamlit. Hệ thống chưa triển khai thành LMS hoàn chỉnh, chưa tích hợp Moodle thật, chưa làm mobile app, chưa fine-tune mô hình ngôn ngữ và chưa xây dựng dashboard giảng viên phức tạp.

## 1.4. Bài toán cần giải quyết

Bài toán đặt ra là làm thế nào để sinh viên có thể upload tài liệu học tập và đặt câu hỏi trực tiếp trên nội dung tài liệu đó. Hệ thống cần đọc được nội dung tài liệu, xử lý thành văn bản sạch, chia thành các đoạn nhỏ, chuyển thành vector embedding, lưu vào vector database và truy xuất các đoạn liên quan nhất khi người dùng đặt câu hỏi.

Sau khi truy xuất được các đoạn tài liệu liên quan, hệ thống cần xây dựng prompt phù hợp để mô hình ngôn ngữ trả lời dựa trên tài liệu tham khảo. Câu trả lời cần rõ ràng, dễ hiểu, không bịa thông tin ngoài tài liệu và có nguồn trích dẫn. Ngoài ra, hệ thống cần lưu lịch sử hỏi đáp để phục vụ việc theo dõi quá trình học tập và làm nền tảng cho các chức năng cá nhân hóa như phát hiện chủ đề yếu, sinh quiz ôn tập và gợi ý học tiếp.

## 1.5. Phương pháp thực hiện

Đề tài được thực hiện theo hướng xây dựng từng thành phần của pipeline RAG. Trước hết, hệ thống được thiết kế cấu trúc project, database và các API cơ bản. Tiếp theo, chức năng upload tài liệu được xây dựng để lưu file gốc và metadata vào database. Sau đó, hệ thống đọc tài liệu, làm sạch văn bản và lưu bản xử lý vào thư mục dữ liệu.

Ở bước xử lý ngữ nghĩa, văn bản được chia thành các chunk có overlap để giữ ngữ cảnh giữa các đoạn. Các chunk được chuyển thành embedding bằng mô hình sentence-transformers hỗ trợ đa ngôn ngữ, phù hợp với tài liệu tiếng Việt. Embedding và metadata của chunk được lưu vào ChromaDB để phục vụ tìm kiếm tương đồng. Khi người dùng đặt câu hỏi, hệ thống tạo embedding cho câu hỏi, truy xuất các chunk liên quan, xây dựng context, tạo prompt và gọi Gemini API để sinh câu trả lời.

Trong quá trình phát triển, hệ thống được kiểm thử qua Swagger và các script test backend. Các kết quả như upload tài liệu, index tài liệu, retrieval, Chat API và lưu lịch sử hỏi đáp được dùng làm minh chứng cho từng giai đoạn thực hiện.

## 1.6. Công nghệ sử dụng

- Backend API: FastAPI được sử dụng để xây dựng các endpoint quản lý người dùng, khóa học, tài liệu, retrieval và chat.
- Database quan hệ: SQLite được sử dụng trong giai đoạn đầu để lưu thông tin người dùng, khóa học, tài liệu và lịch sử hỏi đáp.
- Vector database: ChromaDB được sử dụng để lưu embedding của các chunk tài liệu và hỗ trợ tìm kiếm ngữ nghĩa.
- Embedding model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 được sử dụng vì hỗ trợ đa ngôn ngữ và phù hợp với tài liệu tiếng Việt.
- LLM: Gemini API được sử dụng để sinh câu trả lời dựa trên prompt RAG.
- Xử lý tài liệu: PyMuPDF dùng để đọc PDF, python-docx dùng để đọc DOCX, và xử lý file TXT bằng Python chuẩn.
- Frontend demo: Streamlit được dùng để xây dựng giao diện demo đơn giản cho người dùng.
- Quản lý mã nguồn: Git và GitHub được sử dụng để lưu trữ, quản lý phiên bản và minh chứng tiến độ.

## 1.7. Kết quả dự kiến đạt được

Sau khi hoàn thành, hệ thống dự kiến cho phép sinh viên upload tài liệu học tập, xử lý tài liệu thành text sạch, chia chunk, tạo embedding, lưu vào ChromaDB và tìm kiếm các đoạn liên quan theo câu hỏi. Chatbot có thể trả lời câu hỏi dựa trên tài liệu đã upload và hiển thị nguồn tham khảo.

Hệ thống cũng dự kiến lưu được lịch sử hỏi đáp vào database, bao gồm câu hỏi, câu trả lời, nguồn tham khảo và thời gian phản hồi. Đây là nền tảng để phát triển các chức năng cá nhân hóa như phát hiện topic yếu, sinh quiz ôn tập và gợi ý nội dung học tiếp.

Kết quả demo tối thiểu gồm: Swagger API hoạt động; upload tài liệu thành công; index tài liệu vào vector database; retrieval trả về chunk liên quan; Chat API trả về answer, sources và latency; database có lưu lịch sử chat; và mã nguồn được quản lý trên GitHub.

## 1.8. Bố cục báo cáo

Báo cáo được tổ chức thành các chương chính như sau:

1. Chương 1 trình bày tổng quan đề tài, lý do chọn đề tài, mục tiêu, phạm vi, phương pháp thực hiện và kết quả dự kiến.
2. Chương 2 trình bày cơ sở lý thuyết về chatbot, mô hình ngôn ngữ lớn, RAG, embedding, vector database và các công nghệ liên quan.
3. Chương 3 phân tích yêu cầu và thiết kế hệ thống, bao gồm kiến trúc, luồng xử lý, database và API.
4. Chương 4 trình bày quá trình xây dựng hệ thống, các module backend, xử lý tài liệu, embedding, retrieval và Chat API.
5. Chương 5 trình bày kiểm thử và đánh giá kết quả hệ thống qua các kịch bản upload, index, retrieval và hỏi đáp.
6. Chương 6 trình bày kết luận, hạn chế và hướng phát triển trong tương lai.
