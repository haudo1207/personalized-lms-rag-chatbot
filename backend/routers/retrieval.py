from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.security_deps import get_current_user, verify_course_access
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
def search(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, list[dict[str, object]]]:
    verify_course_access(request.course_id, current_user, db)
    results = retrieve_relevant_chunks(
        question=request.question,
        course_id=request.course_id,
        top_k=request.top_k,
    )
    return {"results": results}
