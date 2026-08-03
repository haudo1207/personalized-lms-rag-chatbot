from backend.services.llm_service import generate_answer


def decompose_query(question: str) -> list[str]:
    """Split a comparison/multi-part question into independent sub-questions,
    each targeting a single fact -- e.g. "INNER JOIN khac LEFT JOIN the nao?"
    becomes two separate lookups ("INNER JOIN la gi?" style) instead of one
    query that has to match both concepts in the same passage. A question
    that's already single-part is returned unchanged.

    Different from query_expansion.generate_query_variants (which rephrases
    the SAME question several ways): this changes WHAT is being asked, not
    just how it's worded, so it's kept as its own retriever toggle."""
    prompt = f"""Nếu câu hỏi sau có tính so sánh hoặc nhiều phần, hãy tách thành các câu hỏi con \
độc lập, mỗi câu hỏi chỉ hỏi về một khái niệm duy nhất, mỗi câu trên một dòng, không đánh số, \
không giải thích gì thêm. Nếu câu hỏi đã đơn giản (một phần, một khái niệm), chỉ trả về đúng \
câu hỏi gốc, không đổi.

Câu hỏi: {question}

Câu hỏi con (hoặc câu hỏi gốc nếu không cần tách):"""
    try:
        raw = generate_answer(prompt)
    except Exception:
        return [question]

    sub_questions = [line.strip("-•* ").strip() for line in raw.strip().splitlines()]
    sub_questions = [q for q in sub_questions if q]
    return sub_questions or [question]
