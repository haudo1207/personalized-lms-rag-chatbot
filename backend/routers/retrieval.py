from fastapi import APIRouter


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.get("/status")
def retrieval_status() -> dict[str, str]:
    return {"status": "planned"}

