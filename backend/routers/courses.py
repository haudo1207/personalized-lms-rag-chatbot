from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.course import Course
from backend.models.user import User
from backend.models.user_course import UserCourse
from backend.security_deps import get_current_user, require_admin


router = APIRouter(prefix="/courses", tags=["Courses"])


class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    description: str | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    course_name: str
    description: str | None
    created_at: datetime


class EnrollRequest(BaseModel):
    user_id: int


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Course:
    new_course = Course(**course.model_dump())
    db.add(new_course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this course_code already exists.",
        ) from exc
    db.refresh(new_course)
    return new_course


@router.get("/", response_model=list[CourseRead])
def get_courses(db: Session = Depends(get_db), _admin: User = Depends(require_admin)) -> list[Course]:
    return db.query(Course).order_by(Course.id).all()


@router.get("/mine", response_model=list[CourseRead])
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Course]:
    if current_user.role == "admin":
        return db.query(Course).order_by(Course.id).all()

    enrolled_ids = [
        row.course_id
        for row in db.query(UserCourse).filter(UserCourse.user_id == current_user.id).all()
    ]
    if not enrolled_ids:
        return []
    return db.query(Course).filter(Course.id.in_(enrolled_ids)).order_by(Course.id).all()


@router.post("/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll_user(
    course_id: int,
    request: EnrollRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> dict[str, object]:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(UserCourse)
        .filter(UserCourse.user_id == request.user_id, UserCourse.course_id == course_id)
        .first()
    )
    if existing:
        return {"message": "User already enrolled", "user_id": request.user_id, "course_id": course_id}

    enrollment = UserCourse(user_id=request.user_id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    return {"message": "Enrolled successfully", "user_id": request.user_id, "course_id": course_id}
