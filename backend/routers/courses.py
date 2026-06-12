from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.course import Course


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


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)) -> Course:
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
def get_courses(db: Session = Depends(get_db)) -> list[Course]:
    return db.query(Course).order_by(Course.id).all()
