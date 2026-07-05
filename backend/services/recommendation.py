from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.weak_topic import WeakTopic


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
        recommendations.append(
            {
                "topic": item.topic,
                "recommendation": (
                    f"Bạn nên ôn lại chủ đề {item.topic}, đọc lại các đoạn tài liệu liên quan "
                    "và làm quiz luyện tập để kiểm tra mức độ hiểu bài."
                ),
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "topic": "Ôn tập chung",
                "recommendation": (
                    "Chưa phát hiện topic yếu rõ ràng. Bạn có thể tiếp tục hỏi chatbot "
                    "và làm quiz theo các chủ đề trọng tâm của môn học."
                ),
            }
        )

    return recommendations
