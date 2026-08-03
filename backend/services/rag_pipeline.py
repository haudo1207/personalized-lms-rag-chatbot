import time

from backend.services.llm_service import generate_answer
from backend.services.prompt_template import (
    INSUFFICIENT_INFORMATION_ANSWER,
    build_personalized_rag_prompt,
)
from backend.services.retriever import retrieve_relevant_chunks


def reorder_for_lost_in_middle(chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    """Move the most relevant chunks to both ends of the list, least relevant to
    the middle. LLMs attend best to the start and end of a long prompt and tend
    to under-use the middle ("Lost in the Middle") -- ranked chunks are zig-zagged
    outward from rank 1 so the top results sit at the two ends instead of being
    front-loaded in descending-rank order."""
    reordered: list[dict[str, object] | None] = [None] * len(chunks)
    left, right = 0, len(chunks) - 1
    for i, chunk in enumerate(chunks):
        if i % 2 == 0:
            reordered[left] = chunk
            left += 1
        else:
            reordered[right] = chunk
            right -= 1
    return [c for c in reordered if c is not None]


def format_context(chunks: list[dict[str, object]]) -> str:
    context_parts: list[str] = []

    for chunk in reorder_for_lost_in_middle(chunks):
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

    # Multi-Query stays off by default. Paired significance test on the dev
    # split (scripts/eval_significance.py, n=40, reciprocal rank, config C vs
    # D): mean 0.807 vs 0.721 favoring plain Hybrid+Reranker, Wilcoxon p=0.0498
    # but the 95% paired bootstrap CI on the difference is [-0.005, +0.192] --
    # right on the edge, not a clean "scores worse" result. What IS unambiguous
    # is latency: 665ms vs 7143ms mean, a >10x cost for a quality gain that
    # isn't clearly real. Keeping only Query Decomposition on-demand, which is
    # cheap to gate (regex heuristic, no LLM cost when it doesn't fire) and
    # targets a real, common study-question pattern (comparison questions).
    chunks = retrieve_relevant_chunks(
        question=search_query,
        course_id=course_id,
        top_k=top_k,
        document_ids=document_ids,
        use_multi_query=False,
        use_query_decomposition="auto",
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
