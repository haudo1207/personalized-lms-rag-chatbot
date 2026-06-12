from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User


router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    full_name: str
    email: str
    role: str = "student"
    level: str = "beginner"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: str
    level: str
    created_at: datetime


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    new_user = User(**user.model_dump())
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc
    db.refresh(new_user)
    return new_user


@router.get("/", response_model=list[UserRead])
def get_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.id).all()
