from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatHistory:
    id: int
    user_id: int
    question: str
    answer: str
    created_at: datetime

