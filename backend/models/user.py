from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="student", nullable=False)
    level = Column(String, default="beginner", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
