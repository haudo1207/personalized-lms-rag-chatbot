from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.weak_topic import WeakTopic
from backend.services.llm_service import generate_answer
from backend.services.rag_pipeline import format_context
from backend.services.retriever import retrieve_relevant_chunks

FALLBACK_RECOMMENDATION = {
    "topic": "Ôn tập chung",
    "recommendation": (
        "Chưa phát hiện topic yếu rõ ràng. Bạn có thể tiếp tục hỏi chatbot "
        "và làm quiz theo các chủ đề trọng tâm của môn học."
    ),
}

_GENERIC_ADVICE = (
    "Bạn nên ôn lại chủ đề {topic}, đọc lại các đoạn tài liệu liên quan "
    "và làm quiz luyện tập để kiểm tra mức độ hiểu bài."
)

# In-memory cache keyed on weak_score (not just topic) so a recommendation
# regenerates once the weak topic's severity actually changes, not on every
# dashboard view. Lost on process restart -- acceptable at this scale; not
# worth resurrecting the unused recommendation_histories table just to
# persist a cache for a value this cheap to regenerate.
_CACHE: dict[tuple, str] = {}


def _generate_recommendation(course_id: int, topic: str) -> str:
    """Grounded in the course's own indexed content (same retrieval pipeline
    as Chat), not a hand-written template -- so this works for any course,
    not just the ones someone thought to write a template for."""
    chunks = retrieve_relevant_chunks(question=topic, course_id=course_id, top_k=3)
    if not chunks:
        return _GENERIC_ADVICE.format(topic=topic)

    context = format_context(chunks)
    prompt = f"""Sinh viên đang yếu ở chủ đề "{topic}". Dựa CHỈ trên các đoạn tài liệu dưới đây, hãy viết
một gợi ý học tập ngắn (2-3 câu): nên ôn lại phần nào, kèm tên tài liệu và số trang nếu đoạn trích có ghi rõ.
Không suy diễn ngoài nội dung tài liệu.

{context}

Gợi ý học tập:"""
    try:
        recommendation = generate_answer(prompt).strip()
        return recommendation or _GENERIC_ADVICE.format(topic=topic)
    except Exception:
        return _GENERIC_ADVICE.format(topic=topic)


def get_recommendations(
    db: Session,
    user_id: int,
    course_id: int,
) -> list[dict[str, str]]:
    weak_topics = (
        db.query(WeakTopic)
        .filter(
            WeakTopic.user_id == user_id,
            WeakTopic.course_id == course_id,
            WeakTopic.status == "active",
        )
        .order_by(WeakTopic.created_at.desc())
        .all()
    )

    recommendations: list[dict[str, str]] = []
    for item in weak_topics:
        cache_key = (user_id, course_id, item.topic, item.weak_score)
        if cache_key not in _CACHE:
            _CACHE[cache_key] = _generate_recommendation(course_id, item.topic)
        recommendations.append({"topic": item.topic, "recommendation": _CACHE[cache_key]})

    if not recommendations:
        recommendations.append(dict(FALLBACK_RECOMMENDATION))

    return recommendations
