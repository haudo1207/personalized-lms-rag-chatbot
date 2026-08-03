from __future__ import annotations

from backend.services.vector_store import get_all_chunks_for_course

MAX_CONTEXT_CHARS = 3000
MAX_DOCUMENTS = 3
CHUNKS_PER_DOCUMENT = 2


def representative_context_for_course(course_id: int) -> str:
    """Picks the earliest chunks (by chunk_index) of each of the first few
    documents in the course -- these tend to be the intro/table-of-contents
    text, a good anchor for "what can I ask about this document?" starter
    questions (question_suggester.py).

    NOT used for topic-taxonomy generation (topic_taxonomy.py) -- a taxonomy
    needs to cover a document's full breadth, not just its introduction, so
    it clusters the whole chunk set by embedding instead of sampling
    positionally. See topic_taxonomy.py's module docstring for why."""
    chunks = get_all_chunks_for_course(course_id)
    by_document: dict[str, list[dict[str, object]]] = {}
    for chunk in chunks:
        doc_id = str(chunk["metadata"].get("document_id"))
        by_document.setdefault(doc_id, []).append(chunk)

    parts: list[str] = []
    total_chars = 0
    for doc_id in list(by_document)[:MAX_DOCUMENTS]:
        doc_chunks = sorted(by_document[doc_id], key=lambda c: int(c["metadata"].get("chunk_index", 0)))
        for chunk in doc_chunks[:CHUNKS_PER_DOCUMENT]:
            text = str(chunk["text"])
            if total_chars + len(text) > MAX_CONTEXT_CHARS:
                break
            parts.append(text)
            total_chars += len(text)

    return "\n\n".join(parts)
