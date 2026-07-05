from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.quiz_result import QuizResult
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
def generate(request: QuizGenerateRequest) -> dict[str, object]:
    try:
        quiz = generate_quiz(
            course_id=request.course_id,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Quiz generation failed: {exc}",
        ) from exc

    return {"quiz": quiz}


@router.post("/submit")
def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
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
) -> list[QuizResult]:
    query = db.query(QuizResult).filter(QuizResult.user_id == user_id)
    if course_id is not None:
        query = query.filter(QuizResult.course_id == course_id)
    return query.order_by(QuizResult.created_at.desc()).all()
