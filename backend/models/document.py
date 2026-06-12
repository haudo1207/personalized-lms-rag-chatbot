from dataclasses import dataclass


@dataclass
class Document:
    id: int
    course_id: int
    filename: str
    file_type: str

