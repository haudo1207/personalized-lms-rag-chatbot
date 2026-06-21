from backend.services.vector_store import search_chunks


def retrieve_relevant_chunks(
    question: str,
    course_id: int,
    top_k: int = 5,
) -> list[dict[str, object]]:
    return search_chunks(question=question, course_id=course_id, top_k=top_k)


def retrieve(question: str, top_k: int = 5) -> list[dict[str, object]]:
    return retrieve_relevant_chunks(question=question, course_id=1, top_k=top_k)
