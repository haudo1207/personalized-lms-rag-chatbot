import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.chat_history import ChatHistory
from backend.services.rag_pipeline import ask_rag


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


@router.post("/")
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        result = ask_rag(
            question=request.question,
            course_id=request.course_id,
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
        sources=json.dumps(result["sources"], ensure_ascii=False),
        latency=str(result["latency"]),
    )

    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    return {
        "chat_id": chat_record.id,
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
