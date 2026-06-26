"""
Minh chung tuan 4: Retrieval API.

File nay gop noi dung chinh cua:
- backend/services/retriever.py
- backend/routers/retrieval.py

Muc dich: nop minh chung bao cao. Code chay that cua du an van nam trong
backend/services/ va backend/routers/.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.vector_store import search_chunks


def retrieve_relevant_chunks(
    question: str,
    course_id: int,
    top_k: int = 5,
) -> list[dict[str, object]]:
    return search_chunks(question=question, course_id=course_id, top_k=top_k)


router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


class RetrievalRequest(BaseModel):
    question: str
    course_id: int
    top_k: int = 5


@router.get("/status")
def retrieval_status() -> dict[str, str]:
    return {"status": "ready"}


@router.post("/search")
def search(request: RetrievalRequest) -> dict[str, list[dict[str, object]]]:
    results = retrieve_relevant_chunks(
        question=request.question,
        course_id=request.course_id,
        top_k=request.top_k,
    )
    return {"results": results}

