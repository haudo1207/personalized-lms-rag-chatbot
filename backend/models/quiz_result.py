from dataclasses import dataclass
from datetime import datetime


@dataclass
class QuizResult:
    id: int
    user_id: int
    topic_name: str
    score: float
    created_at: datetime

