from fastapi import APIRouter


router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/sample")
def sample_quiz() -> dict[str, object]:
    return {
        "topic": "SQL JOIN",
        "questions": [
            {
                "question": "INNER JOIN trả về kết quả nào?",
                "options": [
                    "Các dòng khớp ở cả hai bảng",
                    "Tất cả dòng ở bảng trái",
                    "Tất cả dòng ở bảng phải",
                ],
                "answer": "Các dòng khớp ở cả hai bảng",
            }
        ],
    }

