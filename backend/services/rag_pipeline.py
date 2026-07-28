import time

from backend.services.llm_service import generate_answer
from backend.services.prompt_template import (
    INSUFFICIENT_INFORMATION_ANSWER,
    build_personalized_rag_prompt,
    build_rag_prompt,
)
from backend.services.retriever import retrieve_relevant_chunks


def format_context(chunks: list[dict[str, object]]) -> str:
    context_parts: list[str] = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        source = f"[{metadata['document_name']}, trang {metadata['page']}]"
        context_parts.append(f"{source}\n{chunk['text']}")

    return "\n\n".join(context_parts)


def _build_sources(chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "document_name": chunk["metadata"]["document_name"],
            "page": chunk["metadata"]["page"],
            "content": str(chunk["text"]),
            "distance": chunk.get("distance"),
        }
        for chunk in chunks
    ]


def reformulate_question(question: str, chat_history: list[dict[str, str]] | None) -> str:
    if not chat_history:
        return question
        
    # Take the last 3 exchanges to keep context focused
    history_text = ""
    for item in chat_history[-3:]:
        q = item.get("question", "")
        a = item.get("answer", "")
        history_text += f"Hỏi: {q}\nTrả lời: {a}\n\n"
        
    prompt = f"""Dựa vào lịch sử trò chuyện sau và câu hỏi tiếp theo, hãy viết lại câu hỏi tiếp theo thành một câu hỏi độc lập đầy đủ ngữ cảnh bằng tiếng Việt để tìm kiếm tài liệu. Không giải thích gì thêm, chỉ trả về câu hỏi đã viết lại.

Lịch sử trò chuyện:
{history_text}
Câu hỏi tiếp theo: {question}

Câu hỏi độc lập:"""
    try:
        rewritten = generate_answer(prompt)
        if rewritten.strip():
            return rewritten.strip()
    except Exception:
        pass
    return question


def ask_rag(
    question: str,
    course_id: int,
    top_k: int = 3,
    document_ids: list[int] | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    start_time = time.time()

    # Reformulate question if history exists
    search_query = reformulate_question(question, chat_history)

    chunks = retrieve_relevant_chunks(
        question=search_query,
        course_id=course_id,
        top_k=top_k,
        document_ids=document_ids,
    )
    sources = _build_sources(chunks)

    if not chunks:
        latency = round(time.time() - start_time, 2)
        return {
            "answer": INSUFFICIENT_INFORMATION_ANSWER,
            "sources": sources,
            "latency": latency,
            "search_query": search_query,
        }

    context = format_context(chunks)
    prompt = build_rag_prompt(question=question, context=context)
    answer = generate_answer(prompt)
    latency = round(time.time() - start_time, 2)

    return {
        "answer": answer,
        "sources": sources,
        "latency": latency,
        "search_query": search_query,
    }


def ask_personalized_rag(
    question: str,
    course_id: int,
    user_profile: dict[str, object],
    top_k: int = 3,
    document_ids: list[int] | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    start_time = time.time()

    # Reformulate question if history exists
    search_query = reformulate_question(question, chat_history)

    chunks = retrieve_relevant_chunks(
        question=search_query,
        course_id=course_id,
        top_k=top_k,
        document_ids=document_ids,
    )
    sources = _build_sources(chunks)

    if not chunks:
        latency = round(time.time() - start_time, 2)
        return {
            "answer": INSUFFICIENT_INFORMATION_ANSWER,
            "sources": sources,
            "latency": latency,
            "search_query": search_query,
        }

    context = format_context(chunks)
    prompt = build_personalized_rag_prompt(
        question=question,
        context=context,
        user_profile=user_profile,
    )
    answer = generate_answer(prompt)
    latency = round(time.time() - start_time, 2)

    return {
        "answer": answer,
        "sources": sources,
        "latency": latency,
        "search_query": search_query,
    }


def answer_question(question: str) -> dict[str, object]:
    return ask_rag(question=question, course_id=1)
