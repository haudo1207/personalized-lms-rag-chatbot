from fastapi import APIRouter


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def chat(payload: dict[str, str]) -> dict[str, object]:
    question = payload.get("question", "")
    return {
        "question": question,
        "answer": "RAG pipeline chưa được cài đặt trong tuần 1.",
        "sources": [],
    }

