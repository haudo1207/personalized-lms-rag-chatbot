from __future__ import annotations

import json
import re

from backend.services.course_content_sampler import representative_context_for_course
from backend.services.llm_service import generate_answer


def _extract_questions(text: str) -> list[str]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        array_match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
        if not array_match:
            return []
        parsed = json.loads(array_match.group(0))
    if not isinstance(parsed, list):
        return []
    return [str(q).strip() for q in parsed if str(q).strip()][:4]


def suggest_questions_for_course(course_id: int) -> list[str]:
    context = representative_context_for_course(course_id)
    if not context.strip():
        return []

    prompt = f"""Dựa CHỈ trên nội dung tài liệu dưới đây, hãy đề xuất 3-4 câu hỏi ngắn mà sinh viên
có thể hỏi Chatbot để tìm hiểu tài liệu này. Chỉ tạo câu hỏi có thể trả lời được từ chính nội dung
dưới đây, không suy diễn hay thêm kiến thức ngoài tài liệu.

Nội dung tài liệu:
{context}

Trả về một JSON array các chuỗi câu hỏi, không thêm giải thích ngoài JSON.
Ví dụ định dạng: ["Câu hỏi 1?", "Câu hỏi 2?", "Câu hỏi 3?"]"""

    response = generate_answer(prompt)
    return _extract_questions(response)
