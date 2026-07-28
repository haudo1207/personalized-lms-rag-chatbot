from backend.services.bm25 import BM25
from backend.services.reranker import rerank_chunks
from backend.services.vector_store import get_all_chunks_for_course, search_chunks


def retrieve_relevant_chunks(
    question: str,
    course_id: int,
    top_k: int = 3,
    document_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    # 1. Retrieve top 10 via Vector Search
    vector_results = search_chunks(
        question=question,
        course_id=course_id,
        top_k=10,
        document_ids=document_ids,
    )

    # 2. Retrieve top 10 via BM25
    course_chunks = get_all_chunks_for_course(course_id=course_id, document_ids=document_ids)
    if not course_chunks:
        return vector_results[:top_k]

    bm25_model = BM25(course_chunks)
    bm25_scored = bm25_model.score(question)
    bm25_results = [doc for doc, score in bm25_scored[:10]]

    # 3. Merge Results using Reciprocal Rank Fusion (RRF)
    rrf_scores = {}
    chunk_map = {}

    for rank, chunk in enumerate(vector_results):
        cid = chunk["chunk_id"]
        chunk_map[cid] = chunk
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))

    for rank, chunk in enumerate(bm25_results):
        cid = chunk["chunk_id"]
        chunk_map[cid] = chunk
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60.0 + rank))

    # Sort merged chunks by RRF score
    sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    merged_chunks = [chunk_map[cid] for cid in sorted_cids[:10]]

    # 4. Rerank the top 10 chunks to get the top_k (default 3) most relevant
    reranked = rerank_chunks(question=question, chunks=merged_chunks, top_n=top_k)
    return reranked


def retrieve(
    question: str,
    top_k: int = 3,
    document_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    return retrieve_relevant_chunks(
        question=question,
        course_id=1,
        top_k=top_k,
        document_ids=document_ids,
    )
