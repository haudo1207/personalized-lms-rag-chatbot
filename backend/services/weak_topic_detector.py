from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.chat_history import ChatHistory
from backend.models.weak_topic import WeakTopic


def detect_weak_topic(
    db: Session,
    user_id: int,
    course_id: int,
    topic: str,
    threshold: int = 3,
) -> WeakTopic | None:
    if topic == "Khác":
        return None

    existing = (
        db.query(WeakTopic)
        .filter(
            WeakTopic.user_id == user_id,
            WeakTopic.course_id == course_id,
            WeakTopic.topic == topic,
            WeakTopic.status == "active",
        )
        .first()
    )
    if existing:
        return existing

    topic_question_count = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == user_id,
            ChatHistory.course_id == course_id,
            ChatHistory.topic == topic,
        )
        .count()
    )

    if topic_question_count < threshold:
        return None

    weak_topic = WeakTopic(
        user_id=user_id,
        course_id=course_id,
        topic=topic,
        reason=f"Sinh viên hỏi cùng một chủ đề từ {threshold} lần trở lên.",
    )
    db.add(weak_topic)
    db.commit()
    db.refresh(weak_topic)

    return weak_topic
