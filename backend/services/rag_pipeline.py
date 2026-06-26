import time

from backend.services.llm_service import generate_answer
from backend.services.prompt_template import INSUFFICIENT_INFORMATION_ANSWER, build_rag_prompt
from backend.services.retriever import retrieve_relevant_chunks


def format_context(chunks: list[dict[str, object]]) -> str:
    context_parts: list[str] = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        source = f"[{metadata['document_name']}, trang {metadata['page']}]"
        context_parts.append(f"{source}\n{chunk['text']}")

    return "\n\n".join(context_parts)


def ask_rag(question: str, course_id: int, top_k: int = 5) -> dict[str, object]:
    start_time = time.time()

    chunks = retrieve_relevant_chunks(question=question, course_id=course_id, top_k=top_k)
    sources = [
        {
            "document_name": chunk["metadata"]["document_name"],
            "page": chunk["metadata"]["page"],
            "content": str(chunk["text"])[:300],
            "distance": chunk.get("distance"),
        }
        for chunk in chunks
    ]

    if not chunks:
        latency = round(time.time() - start_time, 2)
        return {
            "answer": INSUFFICIENT_INFORMATION_ANSWER,
            "sources": sources,
            "latency": latency,
        }

    context = format_context(chunks)
    prompt = build_rag_prompt(question=question, context=context)
    answer = generate_answer(prompt)
    latency = round(time.time() - start_time, 2)

    return {
        "answer": answer,
        "sources": sources,
        "latency": latency,
    }


def answer_question(question: str) -> dict[str, object]:
    return ask_rag(question=question, course_id=1)
