from fastapi import APIRouter


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
def list_documents() -> list[dict[str, str]]:
    return []

