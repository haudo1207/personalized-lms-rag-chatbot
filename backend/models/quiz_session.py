from datetime import datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from backend.database import Base

SESSION_LIFETIME_MINUTES = 30


class QuizSession(Base):
    """A generated-but-not-yet-graded quiz. `answer_key` never leaves the
    server -- /quiz/generate only returns `questions` (options, no answers),
    and /quiz/submit grades by comparing submitted answers against this row
    instead of trusting a client-computed score."""

    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    questions = Column(Text, nullable=False)  # JSON: [{question, options, explanation}]
    answer_key = Column(Text, nullable=False)  # JSON: ["A", "C", ...], same order as questions
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(minutes=SESSION_LIFETIME_MINUTES),
        nullable=False,
    )
