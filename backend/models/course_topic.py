from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from backend.database import Base


class CourseTopic(Base):
    """A course's own topic taxonomy -- generated once (from real indexed
    document content, not guessed) when a course first finishes indexing.
    Classification embeds the incoming question and picks the nearest label
    by cosine similarity, so no LLM call happens per question."""

    __tablename__ = "course_topics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON-encoded list[float], already L2-normalized
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
