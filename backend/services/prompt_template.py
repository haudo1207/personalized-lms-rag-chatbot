INSUFFICIENT_INFORMATION_ANSWER = "Tài liệu hiện tại không cung cấp đủ thông tin để trả lời câu hỏi này."


def build_rag_prompt(question: str, context: str) -> str:
    return f"""
Bạn là trợ lý học tập cho sinh viên.

Nhiệm vụ của bạn là trả lời câu hỏi dựa trên TÀI LIỆU THAM KHẢO.

QUY TẮC BẮT BUỘC:
- Chỉ sử dụng thông tin trong tài liệu tham khảo.
- Không bịa thông tin ngoài tài liệu.
- Nếu tài liệu không đủ thông tin, hãy trả lời:
"{INSUFFICIENT_INFORMATION_ANSWER}"
- Trả lời rõ ràng, dễ hiểu.
- Cuối câu trả lời ghi nguồn theo dạng: [Tên tài liệu, trang X].

TÀI LIỆU THAM KHẢO:
{context}

CÂU HỎI:
{question}

TRẢ LỜI:
""".strip()


RAG_PROMPT_TEMPLATE = """Bạn là trợ lý học tập.

Chỉ trả lời dựa trên ngữ cảnh được cung cấp.
Nếu không tìm thấy thông tin, hãy nói rằng tài liệu chưa có đủ dữ liệu.

Ngữ cảnh:
{context}

Câu hỏi:
{question}
"""
