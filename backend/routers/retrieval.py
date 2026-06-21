from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.retriever import retrieve_relevant_chunks


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
