from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float
from backend.database import Base

class WeakTopic(Base):
    __tablename__ = "weak_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    question_frequency = Column(Integer, default=0, nullable=False)
    quiz_average = Column(Float, nullable=True)
    review_interval = Column(Integer, default=0, nullable=False) # in minutes
    weak_score = Column(Float, default=0.0, nullable=False)
    reason = Column(String)
    status = Column(String, default="active", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
