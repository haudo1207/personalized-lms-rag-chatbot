from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.chat_history import ChatHistory
from backend.models.course import Course
from backend.models.course_topic import CourseTopic
from backend.models.document import Document
from backend.models.quiz_result import QuizResult
from backend.models.quiz_session import QuizSession
from backend.models.user import User
from backend.models.weak_topic import WeakTopic
from backend.security_deps import get_current_user, require_admin
from backend.services.vector_store import delete_document_chunks


router = APIRouter(prefix="/courses", tags=["Courses"])


class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    description: str | None = None


class CourseUpdate(BaseModel):
    course_name: str | None = None
    description: str | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    course_name: str
    description: str | None
    owner_id: int | None
    created_at: datetime


def _require_owner_or_admin(course: Course, current_user: User) -> None:
    if current_user.role != "admin" and course.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thao tác trên môn học của người khác.",
        )


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Course:
    """Ownership-based: any authenticated user creates their own course
    workspace -- there is no admin-only setup step in this model."""
    new_course = Course(**course.model_dump(), owner_id=current_user.id)
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
def get_courses(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[Course]:
    return db.query(Course).order_by(Course.id).all()


@router.get("/mine", response_model=list[CourseRead])
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Course]:
    return db.query(Course).filter(Course.owner_id == current_user.id).order_by(Course.id).all()


@router.patch("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    update: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_owner_or_admin(course, current_user)

    data = update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_200_OK)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Hard delete: there is no archive/restore state in the ownership model
    (each course belongs to exactly one student), so removing a course also
    removes everything scoped to it -- vector chunks, raw files, documents,
    chat history, quiz sessions/results, weak topics and recommendations.
    This is irreversible; the UI must confirm before calling this."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    _require_owner_or_admin(course, current_user)

    documents = db.query(Document).filter(Document.course_id == course_id).all()
    for document in documents:
        delete_document_chunks(document.id)
        raw_path = Path(document.file_path)
        if raw_path.exists():
            raw_path.unlink()
        db.delete(document)

    db.query(ChatHistory).filter(ChatHistory.course_id == course_id).delete()
    db.query(QuizResult).filter(QuizResult.course_id == course_id).delete()
    db.query(QuizSession).filter(QuizSession.course_id == course_id).delete()
    db.query(WeakTopic).filter(WeakTopic.course_id == course_id).delete()
    db.query(CourseTopic).filter(CourseTopic.course_id == course_id).delete()

    db.delete(course)
    db.commit()
    return {"message": "Course deleted", "course_id": course_id}
