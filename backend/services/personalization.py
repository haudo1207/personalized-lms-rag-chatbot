from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.chat_history import ChatHistory
from backend.models.user import User
from backend.models.weak_topic import WeakTopic


def get_recent_questions(db: Session, user_id: int, limit: int = 5) -> list[str]:
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    return [chat.question for chat in chats]


def get_weak_topics(db: Session, user_id: int, course_id: int) -> list[str]:
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

    return [item.topic for item in weak_topics]


def build_user_profile(db: Session, user_id: int, course_id: int) -> dict[str, object]:
    user = db.query(User).filter(User.id == user_id).first()

    return {
        "user_id": user_id,
        "full_name": user.full_name if user else "Unknown user",
        "level": user.level if user else "beginner",
        "recent_questions": get_recent_questions(db, user_id),
        "weak_topics": get_weak_topics(db, user_id, course_id),
    }
