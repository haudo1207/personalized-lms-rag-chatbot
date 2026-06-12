def recommend_next_topics(weak_topics: list[str]) -> list[str]:
    if weak_topics:
        return weak_topics
    return ["SQL JOIN", "Chuẩn hóa dữ liệu"]

