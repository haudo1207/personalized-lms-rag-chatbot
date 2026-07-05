INSUFFICIENT_INFORMATION_ANSWER = (
    "Tài liệu hiện tại không cung cấp đủ thông tin để trả lời câu hỏi này."
)


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


def build_personalized_rag_prompt(
    question: str,
    context: str,
    user_profile: dict[str, object],
) -> str:
    weak_topics = user_profile.get("weak_topics", [])
    recent_questions = user_profile.get("recent_questions", [])
    weak_topic_text = ", ".join(str(topic) for topic in weak_topics) or "Chưa có"

    return f"""
Bạn là trợ lý học tập cá nhân hóa cho sinh viên.

THÔNG TIN NGƯỜI HỌC:
- Họ tên: {user_profile.get("full_name", "Unknown user")}
- Trình độ: {user_profile.get("level", "beginner")}
- Chủ đề còn yếu: {weak_topic_text}
- Câu hỏi gần đây: {recent_questions}

TÀI LIỆU THAM KHẢO:
{context}

CÂU HỎI:
{question}

QUY TẮC:
- Chỉ trả lời dựa trên tài liệu tham khảo.
- Không bịa thông tin ngoài tài liệu.
- Nếu tài liệu không đủ thông tin, hãy trả lời: "{INSUFFICIENT_INFORMATION_ANSWER}"
- Nếu người học là beginner, giải thích đơn giản, từng bước và có ví dụ dễ hiểu.
- Nếu người học là advanced, có thể dùng thuật ngữ chuyên môn hơn và trả lời cô đọng hơn.
- Nếu câu hỏi liên quan đến topic yếu, hãy giải thích kỹ hơn và nhắc lại ý chính.
- Cuối câu trả lời ghi nguồn theo dạng: [Tên tài liệu, trang X].

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
