from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.security_deps import get_current_user, require_self_or_admin, verify_course_access
from backend.services.dashboard_service import get_student_dashboard
from backend.services.recommendation import get_recommendations


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/student/{user_id}")
def student_dashboard(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    require_self_or_admin(user_id, current_user)
    verify_course_access(course_id, current_user, db)
    dashboard = get_student_dashboard(db=db, user_id=user_id, course_id=course_id)
    recommendations = get_recommendations(db=db, user_id=user_id, course_id=course_id)

    return {
        **dashboard,
        "recommendations": recommendations,
    }


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)) -> dict[str, object]:
    return {
        "message": "Use /dashboard/student/{user_id}?course_id=... for the student dashboard.",
    }
