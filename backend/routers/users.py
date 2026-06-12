from fastapi import APIRouter


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def list_users() -> list[dict[str, str]]:
    return [{"id": "student_demo", "learning_level": "basic"}]

