from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from backend.database import Base


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=False)
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
