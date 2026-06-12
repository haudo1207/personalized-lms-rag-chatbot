def detect_weak_topics(quiz_results: list[dict[str, object]], threshold: float = 0.6) -> list[str]:
    weak_topics: list[str] = []
    for result in quiz_results:
        score = float(result.get("score", 0))
        topic = str(result.get("topic", ""))
        if topic and score < threshold:
            weak_topics.append(topic)
    return weak_topics

