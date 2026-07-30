from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.security_deps import get_current_user, require_admin, require_self_or_admin
from backend.services.auth_service import hash_password


router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
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
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    data = user.model_dump()
    password = data.pop("password")
    new_user = User(**data, password_hash=hash_password(password))
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
def get_users(db: Session = Depends(get_db), _admin: User = Depends(require_admin)) -> list[User]:
    return db.query(User).order_by(User.id).all()


@router.patch("/{user_id}/level", response_model=UserRead)
def update_user_level(
    user_id: int,
    level: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    require_self_or_admin(user_id, current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if level not in {"beginner", "intermediate", "advanced"}:
        raise HTTPException(status_code=400, detail="Invalid level. Choose beginner, intermediate, or advanced.")
    user.level = level
    db.commit()
    db.refresh(user)
    return user
