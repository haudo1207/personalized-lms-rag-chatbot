import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.quiz_result import QuizResult
from backend.models.quiz_session import QuizSession
from backend.models.user import User
from backend.security_deps import get_current_user, require_self_or_admin, verify_course_access
from backend.services.quiz_generator import generate_quiz


router = APIRouter(prefix="/quiz", tags=["Quiz"])


class QuizGenerateRequest(BaseModel):
    user_id: int
    course_id: int
    topic: str
    num_questions: int = Field(default=5, ge=1, le=10)
    difficulty: str = "easy"


class QuizSubmitRequest(BaseModel):
    user_id: int
    course_id: int
    quiz_session_id: int
    answers: list[str | None]


class QuizResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    topic: str
    score: float
    total_questions: int | None
    correct_answers: int | None
    created_at: datetime


@router.post("/generate")
def generate(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    require_self_or_admin(request.user_id, current_user)
    verify_course_access(request.course_id, current_user, db)

    # 1. Determine adaptive difficulty based on past performance
    latest_result = (
        db.query(QuizResult)
        .filter(
            QuizResult.user_id == request.user_id,
            QuizResult.course_id == request.course_id,
            QuizResult.topic == request.topic,
        )
        .order_by(QuizResult.created_at.desc())
        .first()
    )

    difficulty = request.difficulty
    if latest_result:
        if latest_result.score >= 80.0:
            difficulty = "hard"
        elif latest_result.score < 50.0:
            difficulty = "easy"
        else:
            difficulty = "medium"
    else:
        difficulty = "easy"

    try:
        quiz = generate_quiz(
            course_id=request.course_id,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=difficulty,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz generation failed: {exc}",
        ) from exc

    if isinstance(quiz, dict):
        # generate_quiz() reports "no context" / "could not parse" this way; nothing to grade.
        return {"quiz": quiz, "adaptive_difficulty": difficulty}

    # Persist the full quiz (incl. correct_answer + explanation) server-side and
    # only ever hand the client question/options -- /quiz/submit grades against
    # this row instead of trusting a client-computed score.
    answer_key = [str(item.get("correct_answer", "")).strip().upper() for item in quiz]
    session = QuizSession(
        user_id=request.user_id,
        course_id=request.course_id,
        topic=request.topic,
        difficulty=difficulty,
        questions=json.dumps(quiz, ensure_ascii=False),
        answer_key=json.dumps(answer_key, ensure_ascii=False),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    sanitized_quiz = [
        {"question": item.get("question", ""), "options": item.get("options", {})} for item in quiz
    ]

    return {
        "quiz_session_id": session.id,
        "quiz": sanitized_quiz,
        "adaptive_difficulty": difficulty,
        "expires_at": session.expires_at.isoformat(),
    }


@router.post("/submit")
def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    require_self_or_admin(request.user_id, current_user)
    verify_course_access(request.course_id, current_user, db)

    session = db.query(QuizSession).filter(QuizSession.id == request.quiz_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found.")
    if session.user_id != request.user_id:
        raise HTTPException(status_code=403, detail="This quiz session belongs to a different user.")
    if session.used:
        raise HTTPException(status_code=409, detail="This quiz session has already been submitted.")
    if datetime.utcnow() > session.expires_at:
        raise HTTPException(status_code=410, detail="This quiz session has expired. Please generate a new quiz.")

    questions: list[dict[str, object]] = json.loads(session.questions)
    answer_key: list[str] = json.loads(session.answer_key)
    if len(request.answers) != len(answer_key):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(answer_key)} answers, received {len(request.answers)}.",
        )

    review: list[dict[str, object]] = []
    correct_count = 0
    for question, correct_letter, selected in zip(questions, answer_key, request.answers):
        selected_letter = selected.strip().upper() if selected else None
        is_correct = selected_letter == correct_letter
        if is_correct:
            correct_count += 1
        review.append(
            {
                "question": question.get("question", ""),
                "options": question.get("options", {}),
                "selected": selected_letter,
                "correct": correct_letter,
                "is_correct": is_correct,
                "explanation": question.get("explanation"),
            }
        )

    total_questions = len(answer_key)
    score = round(correct_count / total_questions * 100, 2) if total_questions else 0.0

    result = QuizResult(
        user_id=request.user_id,
        course_id=request.course_id,
        topic=session.topic,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_count,
    )
    db.add(result)
    session.used = True
    db.commit()
    db.refresh(result)

    return {
        "message": "Quiz result saved",
        "quiz_result_id": result.id,
        "score": score,
        "correct_answers": correct_count,
        "total_questions": total_questions,
        "review": review,
    }


@router.get("/results/{user_id}", response_model=list[QuizResultRead])
def get_quiz_results(
    user_id: int,
    course_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QuizResult]:
    require_self_or_admin(user_id, current_user)
    if course_id is not None:
        verify_course_access(course_id, current_user, db)
    query = db.query(QuizResult).filter(QuizResult.user_id == user_id)
    if course_id is not None:
        query = query.filter(QuizResult.course_id == course_id)
    return query.order_by(QuizResult.created_at.desc()).all()
