import time

from backend.services.bm25 import BM25
from backend.services.reranker import rerank_chunks
from backend.services.vector_store import get_all_chunks_for_course, get_collection_count, search_chunks

DENSE_CANDIDATES = 10
BM25_CANDIDATES = 10
RRF_K = 60.0

_BM25_CACHE: dict[tuple, tuple[int, "BM25 | None", list[dict]]] = {}


def _bm25_cache_key(course_id: int, document_ids: list[int] | None) -> tuple:
    return (course_id, tuple(sorted(document_ids)) if document_ids else None)


def _get_bm25_index(course_id: int, document_ids: list[int] | None):
    key = _bm25_cache_key(course_id, document_ids)
    stamp = get_collection_count()
    cached = _BM25_CACHE.get(key)
    if cached is not None and cached[0] == stamp:
        return cached[1], cached[2]

    chunks = get_all_chunks_for_course(course_id=course_id, document_ids=document_ids)
    model = BM25(chunks) if chunks else None
    _BM25_CACHE[key] = (stamp, model, chunks)
    return model, chunks


def reset_bm25_cache() -> None:
    _BM25_CACHE.clear()


def retrieve_ranked(
    question: str,
    course_id: int,
    top_k: int = 3,
    document_ids: list[int] | None = None,
    *,
    use_bm25: bool = True,
    use_reranker: bool = True,
    dense_candidates: int = DENSE_CANDIDATES,
    bm25_candidates: int = BM25_CANDIDATES,
    fusion_candidates: int = DENSE_CANDIDATES,
    rrf_k: float = RRF_K,
    timings: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    t0 = time.perf_counter()

    # 1. Dense (vector) search
    vector_results = search_chunks(
        question=question,
        course_id=course_id,
        top_k=dense_candidates,
        document_ids=document_ids,
    )
    t1 = time.perf_counter()
    if timings is not None:
        timings["dense_ms"] = (t1 - t0) * 1000

    if not use_bm25:
        fused = vector_results[:fusion_candidates]
        if timings is not None:
            timings["bm25_ms"] = 0.0
            timings["fusion_ms"] = 0.0
    else:
        bm25_model, _course_chunks = _get_bm25_index(course_id, document_ids)
        t2 = time.perf_counter()
        if timings is not None:
            timings["bm25_ms"] = (t2 - t1) * 1000

        if bm25_model is None:
            # BM25 corpus empty (e.g. course not yet indexed) -- explicit fallback to dense-only,
            # not a silent one: caller can see this via the empty bm25_ms/fusion_ms below.
            fused = vector_results[:fusion_candidates]
            if timings is not None:
                timings["fusion_ms"] = 0.0
        else:
            bm25_scored = bm25_model.score(question)
            bm25_results = [doc for doc, _score in bm25_scored[:bm25_candidates]]

            # Reciprocal Rank Fusion (RRF)
            rrf_scores: dict[str, float] = {}
            chunk_map: dict[str, dict] = {}

            for rank, chunk in enumerate(vector_results):
                cid = chunk["chunk_id"]
                chunk_map[cid] = chunk
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

            for rank, chunk in enumerate(bm25_results):
                cid = chunk["chunk_id"]
                chunk_map[cid] = chunk
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

            sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
            fused = [chunk_map[cid] for cid in sorted_cids[:fusion_candidates]]

            if timings is not None:
                timings["fusion_ms"] = (time.perf_counter() - t2) * 1000

    if not use_reranker:
        if timings is not None:
            timings["rerank_ms"] = 0.0
            timings["total_ms"] = (time.perf_counter() - t0) * 1000
        return fused[:top_k]

    t3 = time.perf_counter()
    reranked = rerank_chunks(question=question, chunks=fused, top_n=top_k)
    if timings is not None:
        timings["rerank_ms"] = (time.perf_counter() - t3) * 1000
        timings["total_ms"] = (time.perf_counter() - t0) * 1000
    return reranked


def retrieve_relevant_chunks(
    question: str,
    course_id: int,
    top_k: int = 3,
    document_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    return retrieve_ranked(question, course_id, top_k, document_ids)


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
