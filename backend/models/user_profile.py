from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float
from backend.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    learning_level = Column(String, default="beginner", nullable=False)
    recent_questions = Column(Integer, default=0, nullable=False)
    weak_topics = Column(String, default="", nullable=False) # comma-separated list of topics
    quiz_average = Column(Float, default=0.0, nullable=False)
    learning_frequency = Column(Float, default=0.0, nullable=False) # questions per week
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False)
