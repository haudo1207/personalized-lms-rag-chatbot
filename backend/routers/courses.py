from fastapi import APIRouter


router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/")
def list_courses() -> list[dict[str, str]]:
    return [{"id": "database", "name": "Cơ sở dữ liệu"}]

