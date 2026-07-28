from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.chat_history import ChatHistory
from backend.models.quiz_result import QuizResult
from backend.models.weak_topic import WeakTopic


def detect_weak_topic(
    db: Session,
    user_id: int,
    course_id: int,
    topic: str,
    threshold: float = 0.4,
) -> WeakTopic | None:
    if topic == "Khác":
        return None

    # 1. Calculate Question Frequency score (q_score: max 1.0 for 5+ questions)
    chats = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == user_id,
            ChatHistory.course_id == course_id,
            ChatHistory.topic == topic,
        )
        .all()
    )
    question_count = len(chats)
    q_score = min(question_count / 5.0, 1.0)

    # 2. Calculate Quiz Score Weakness (quiz_weakness: higher when score is lower)
    quiz_results = (
        db.query(QuizResult)
        .filter(
            QuizResult.user_id == user_id,
            QuizResult.course_id == course_id,
            QuizResult.topic == topic,
        )
        .all()
    )
    if quiz_results:
        avg_score = sum(q.score for q in quiz_results) / len(quiz_results)
        quiz_weakness = 1.0 - (avg_score / 100.0)
    else:
        avg_score = None
        quiz_weakness = 0.0

    # 3. Calculate Study Time Weakness (cramming index: higher when questions are asked in quick succession)
    if question_count >= 2:
        timestamps = [c.created_at for c in chats]
        min_time = min(timestamps)
        max_time = max(timestamps)
        time_diff_min = (max_time - min_time).total_seconds() / 60.0
        # Spread study target: 120 minutes (2 hours)
        study_time_score = min(time_diff_min / 120.0, 1.0)
        time_weakness = 1.0 - study_time_score
    else:
        time_diff_min = 0.0
        time_weakness = 1.0

    # 4. Compute composite Weak Score
    # weak_score = 0.4 * q_score + 0.4 * quiz_weakness + 0.2 * time_weakness
    weak_score = round(0.4 * q_score + 0.4 * quiz_weakness + 0.2 * time_weakness, 2)

    # 5. If weak score is below threshold, resolve any existing active weak topic
    if weak_score < threshold:
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
            existing.status = "resolved"
            db.commit()
        return None

    # 6. Retrieve or create active weak topic with analytics reason
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

    reason = (
        f"Chỉ số yếu: {weak_score} | Số lần hỏi: {question_count} | "
        f"Điểm quiz trung bình: {f'{avg_score:.1f}%' if avg_score is not None else 'Chưa làm quiz'} | "
        f"Chỉ số học tập dồn dập (Cramming): {time_weakness * 100:.0f}%"
    )

    if existing:
        existing.reason = reason
        existing.question_frequency = question_count
        existing.quiz_average = avg_score
        existing.review_interval = int(time_diff_min)
        existing.weak_score = weak_score
        db.commit()
        db.refresh(existing)
        return existing

    weak_topic = WeakTopic(
        user_id=user_id,
        course_id=course_id,
        topic=topic,
        reason=reason,
        question_frequency=question_count,
        quiz_average=avg_score,
        review_interval=int(time_diff_min),
        weak_score=weak_score,
        status="active",
    )
    db.add(weak_topic)
    db.commit()
    db.refresh(weak_topic)

    return weak_topic
