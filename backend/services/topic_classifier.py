from __future__ import annotations

import unicodedata


def _normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text.replace("đ", "d")


def classify_topic(question: str) -> str:
    normalized = _normalize(question)

    if "khoa chinh" in normalized or "primary key" in normalized:
        return "Khóa chính"

    if "khoa ngoai" in normalized or "foreign key" in normalized:
        return "Khóa ngoại"

    if "join" in normalized:
        return "SQL JOIN"

    if any(keyword in normalized for keyword in ["chuan hoa", "1nf", "2nf", "3nf"]):
        return "Chuẩn hóa cơ sở dữ liệu"

    if any(keyword in normalized for keyword in ["erd", "thuc the", "moi quan he"]):
        return "ERD"

    return "Khác"
