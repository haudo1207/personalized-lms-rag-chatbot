from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    learning_level: str = "basic"

