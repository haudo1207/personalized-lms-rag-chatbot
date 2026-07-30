import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.chat_history import ChatHistory
from backend.models.user import User
from backend.models.weak_topic import WeakTopic
from backend.security_deps import get_current_user, require_self_or_admin, verify_course_access
from backend.services.personalization import build_user_profile
from backend.services.rag_pipeline import ask_personalized_rag
from backend.services.topic_classifier import classify_topic
from backend.services.weak_topic_detector import detect_weak_topic


router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    user_id: int
    course_id: int
    question: str
    top_k: int = 3
    document_ids: list[int] | None = None


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
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    require_self_or_admin(request.user_id, current_user)
    verify_course_access(request.course_id, current_user, db)

    topic = classify_topic(request.question)
    user_profile = build_user_profile(
        db=db,
        user_id=request.user_id,
        course_id=request.course_id,
    )

    # Retrieve chat history memory for query reformulation
    db_history = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == request.user_id,
            ChatHistory.course_id == request.course_id,
        )
        .order_by(ChatHistory.created_at.desc())
        .limit(5)
        .all()
    )
    chat_history = [
        {"question": chat.question, "answer": chat.answer}
        for chat in reversed(db_history)
    ]

    try:
        result = ask_personalized_rag(
            question=request.question,
            course_id=request.course_id,
            user_profile=user_profile,
            top_k=request.top_k,
            document_ids=request.document_ids,
            chat_history=chat_history,
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
def get_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatHistory]:
    require_self_or_admin(user_id, current_user)
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )


@router.get("/profile/{user_id}/{course_id}")
def get_profile(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    require_self_or_admin(user_id, current_user)
    verify_course_access(course_id, current_user, db)
    return build_user_profile(db=db, user_id=user_id, course_id=course_id)


@router.get("/weak-topics/{user_id}/{course_id}", response_model=list[WeakTopicRead])
def list_weak_topics(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WeakTopic]:
    require_self_or_admin(user_id, current_user)
    verify_course_access(course_id, current_user, db)
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
