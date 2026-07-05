import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.chat_history import ChatHistory
from backend.models.weak_topic import WeakTopic
from backend.services.personalization import build_user_profile
from backend.services.rag_pipeline import ask_personalized_rag
from backend.services.topic_classifier import classify_topic
from backend.services.weak_topic_detector import detect_weak_topic


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    user_id: int
    course_id: int
    question: str
    top_k: int = 5


class ChatHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    question: str
    answer: str
    topic: str | None
    sources: str | None
    latency: str | None
    created_at: datetime


class WeakTopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    topic: str
    reason: str | None
    status: str
    created_at: datetime


@router.post("/")
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    topic = classify_topic(request.question)
    user_profile = build_user_profile(
        db=db,
        user_id=request.user_id,
        course_id=request.course_id,
    )

    try:
        result = ask_personalized_rag(
            question=request.question,
            course_id=request.course_id,
            user_profile=user_profile,
            top_k=request.top_k,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM request failed: {exc}",
        ) from exc

    chat_record = ChatHistory(
        user_id=request.user_id,
        course_id=request.course_id,
        question=request.question,
        answer=str(result["answer"]),
        topic=topic,
        sources=json.dumps(result["sources"], ensure_ascii=False),
        latency=str(result["latency"]),
    )

    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    weak_topic = detect_weak_topic(
        db=db,
        user_id=request.user_id,
        course_id=request.course_id,
        topic=topic,
    )

    return {
        "chat_id": chat_record.id,
        "topic": topic,
        "weak_topic": weak_topic.topic if weak_topic else None,
        "user_profile": user_profile,
        **result,
    }


@router.get("/history/{user_id}", response_model=list[ChatHistoryRead])
def get_history(user_id: int, db: Session = Depends(get_db)) -> list[ChatHistory]:
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )


@router.get("/profile/{user_id}/{course_id}")
def get_profile(user_id: int, course_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    return build_user_profile(db=db, user_id=user_id, course_id=course_id)


@router.get("/weak-topics/{user_id}/{course_id}", response_model=list[WeakTopicRead])
def list_weak_topics(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db),
) -> list[WeakTopic]:
    return (
        db.query(WeakTopic)
        .filter(
            WeakTopic.user_id == user_id,
            WeakTopic.course_id == course_id,
            WeakTopic.status == "active",
        )
        .order_by(WeakTopic.created_at.desc())
        .all()
    )
