TOPICS = ["Khóa chính", "Khóa ngoại", "SQL JOIN", "Chuẩn hóa dữ liệu", "ERD", "1NF", "2NF", "3NF"]


def classify_topic(text: str) -> str:
    lowered = text.lower()
    for topic in TOPICS:
        if topic.lower() in lowered:
            return topic
    return "Chưa phân loại"

