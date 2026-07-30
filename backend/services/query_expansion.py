from backend.services.llm_service import generate_answer


def generate_query_variants(question: str, n: int = 3) -> list[str]:
    """Ask the LLM for n alternate phrasings of question, to widen recall when
    the user's wording is short or ambiguous (Multi-Query expansion). Falls back
    to an empty list on any failure -- the caller always still has the original
    question to search with."""
    prompt = f"""Viết lại câu hỏi sau thành {n} câu hỏi khác nhau về cách diễn đạt nhưng giữ nguyên ý nghĩa, \
để tìm kiếm tài liệu tốt hơn. Mỗi câu hỏi trên một dòng, không đánh số, không giải thích gì thêm.

Câu hỏi gốc: {question}

{n} câu hỏi viết lại:"""
    try:
        raw = generate_answer(prompt)
    except Exception:
        return []

    variants = [line.strip("-•* ").strip() for line in raw.strip().splitlines()]
    variants = [v for v in variants if v]
    return variants[:n]
