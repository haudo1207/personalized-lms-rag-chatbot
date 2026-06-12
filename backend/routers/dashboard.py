from fastapi import APIRouter


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary() -> dict[str, object]:
    return {
        "documents": 0,
        "questions": 0,
        "weak_topics": [],
    }

