from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.chat_history import ChatHistory
from backend.models.quiz_result import QuizResult
from backend.models.weak_topic import WeakTopic


def get_student_dashboard(
    db: Session,
    user_id: int,
    course_id: int,
) -> dict[str, object]:
    total_questions = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == user_id,
            ChatHistory.course_id == course_id,
        )
        .count()
    )

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

    quiz_results = (
        db.query(QuizResult)
        .filter(
            QuizResult.user_id == user_id,
            QuizResult.course_id == course_id,
        )
        .order_by(QuizResult.created_at.desc())
        .all()
    )

    average_quiz_score = None
    if quiz_results:
        average_quiz_score = round(
            sum(float(item.score) for item in quiz_results) / len(quiz_results),
            2,
        )

    return {
        "total_questions": total_questions,
        "weak_topics": [item.topic for item in weak_topics],
        "quiz_results": [
            {
                "topic": item.topic,
                "score": item.score,
                "correct_answers": item.correct_answers,
                "total_questions": item.total_questions,
                "created_at": item.created_at,
            }
            for item in quiz_results
        ],
        "average_quiz_score": average_quiz_score,
    }
