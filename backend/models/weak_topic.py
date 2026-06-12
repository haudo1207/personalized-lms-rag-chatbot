from dataclasses import dataclass


@dataclass
class WeakTopic:
    id: int
    user_id: int
    topic_name: str
    score: float

