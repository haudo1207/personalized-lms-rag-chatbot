from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from backend.database import Base


class WeakTopic(Base):
    __tablename__ = "weak_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    reason = Column(String)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
