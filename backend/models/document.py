from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from backend.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    status = Column(String, default="uploaded", nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
