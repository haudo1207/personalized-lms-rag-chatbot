from __future__ import annotations

import json
import re
from typing import Any

from backend.services.llm_service import generate_answer
from backend.services.rag_pipeline import format_context
from backend.services.retriever import retrieve_relevant_chunks


def build_quiz_prompt(
    context: str,
    topic: str,
    num_questions: int = 5,
    difficulty: str = "easy",
) -> str:
    return f"""
Bạn là hệ thống tạo câu hỏi ôn tập cho sinh viên.

Dựa trên tài liệu sau:
{context}

Hãy tạo {num_questions} câu hỏi trắc nghiệm về chủ đề: {topic}.
Độ khó: {difficulty}

Yêu cầu:
- Mỗi câu có 4 lựa chọn A, B, C, D.
- Chỉ có 1 đáp án đúng.
- Có giải thích ngắn cho đáp án đúng.
- Không tạo câu hỏi ngoài nội dung tài liệu.
- Trả về JSON hợp lệ, không thêm giải thích ngoài JSON.

Định dạng:
[
  {{
    "question": "...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "correct_answer": "A",
    "explanation": "..."
  }}
]
""".strip()


def _extract_json(text: str) -> Any:
    cleaned = text.strip()
    fenced_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        cleaned = fenced_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        array_match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
        if array_match:
            return json.loads(array_match.group(0))
        raise


def generate_quiz(
    course_id: int,
    topic: str,
    num_questions: int = 5,
    difficulty: str = "easy",
) -> list[dict[str, Any]] | dict[str, str]:
    chunks = retrieve_relevant_chunks(question=topic, course_id=course_id, top_k=5)
    context = format_context(chunks)

    if not context.strip():
        return {
            "error": "No relevant context found",
            "raw_response": "Không tìm thấy nội dung phù hợp trong tài liệu để tạo quiz.",
        }

    prompt = build_quiz_prompt(
        context=context,
        topic=topic,
        num_questions=num_questions,
        difficulty=difficulty,
    )
    response = generate_answer(prompt)

    try:
        quiz = _extract_json(response)
    except Exception:
        return {
            "error": "Could not parse JSON",
            "raw_response": response,
        }

    if not isinstance(quiz, list):
        return {
            "error": "Quiz response is not a JSON array",
            "raw_response": json.dumps(quiz, ensure_ascii=False),
        }

    return quiz
