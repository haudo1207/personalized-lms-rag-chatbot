from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.quiz_result import QuizResult
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
    topic: str
    total_questions: int = Field(ge=1)
    correct_answers: int = Field(ge=0)


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

    return {"quiz": quiz, "adaptive_difficulty": difficulty}


@router.post("/submit")
def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    require_self_or_admin(request.user_id, current_user)
    verify_course_access(request.course_id, current_user, db)

    if request.correct_answers > request.total_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="correct_answers cannot be greater than total_questions.",
        )

    score = round(request.correct_answers / request.total_questions * 100, 2)
    result = QuizResult(
        user_id=request.user_id,
        course_id=request.course_id,
        topic=request.topic,
        score=score,
        total_questions=request.total_questions,
        correct_answers=request.correct_answers,
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "message": "Quiz result saved",
        "quiz_result_id": result.id,
        "score": score,
        "correct_answers": result.correct_answers,
        "total_questions": result.total_questions,
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
