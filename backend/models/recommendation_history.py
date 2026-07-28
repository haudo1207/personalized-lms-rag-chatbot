from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from backend.database import Base

class RecommendationHistory(Base):
    __tablename__ = "recommendation_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    recommendation_text = Column(Text, nullable=False)
    status = Column(String, default="unread", nullable=False) # unread, read
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
