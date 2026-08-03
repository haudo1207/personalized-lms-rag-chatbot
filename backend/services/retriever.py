import time

from backend.services.bm25 import BM25
from backend.services.query_decomposition import decompose_query
from backend.services.query_expansion import generate_query_variants
from backend.services.query_router import is_complex_question
from backend.services.reranker import rerank_chunks
from backend.services.vector_store import get_all_chunks_for_course, get_collection_count, search_chunks

DENSE_CANDIDATES = 10
BM25_CANDIDATES = 10
RRF_K = 60.0
MULTI_QUERY_N = 3
# Reranker score (CrossEncoder logit, unbounded) below which the top-1 result of the
# first single-query pass is treated as low-confidence and worth retrying with
# Multi-Query variants. Calibrated on the 50-question eval set (Config C, single
# pass): the 40 hit@3 questions average rerank_score=4.52 (range -3.78..10.67), the
# 10 miss questions average -1.34 (range -5.33..3.18). threshold=1.0 catches 9/10
# misses while only re-triggering the expensive path for 19/50 (38%) of questions.
MULTI_QUERY_CONFIDENCE_THRESHOLD = 1.0

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


def _merge_queries_into_fusion(
    queries: list[str],
    course_id: int,
    document_ids: list[int] | None,
    dense_candidates: int,
    bm25_model: "BM25 | None",
    bm25_candidates: int,
    rrf_k: float,
    chunk_map: dict[str, dict],
    rrf_scores: dict[str, float],
) -> None:
    """Run dense (+ BM25, if bm25_model given) search for each query, merging RRF
    scores into chunk_map/rrf_scores in place. Used for the Multi-Query "auto" retry
    pass so the fusion logic isn't duplicated -- the main first pass below keeps its
    own inline loop (unchanged) so its per-stage timings stay exactly as before."""
    for query in queries:
        vector_results = search_chunks(
            question=query, course_id=course_id, top_k=dense_candidates, document_ids=document_ids
        )
        for rank, chunk in enumerate(vector_results):
            cid = chunk["chunk_id"]
            chunk_map.setdefault(cid, chunk)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
        if bm25_model is not None:
            bm25_scored = bm25_model.score(query)
            bm25_results = [doc for doc, _score in bm25_scored[:bm25_candidates]]
            for rank, chunk in enumerate(bm25_results):
                cid = chunk["chunk_id"]
                chunk_map.setdefault(cid, chunk)
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))


def retrieve_ranked(
    question: str,
    course_id: int,
    top_k: int = 3,
    document_ids: list[int] | None = None,
    *,
    use_bm25: bool = True,
    use_reranker: bool = True,
    use_multi_query: bool | str = False,
    multi_query_n: int = MULTI_QUERY_N,
    use_query_decomposition: bool | str = False,
    dense_candidates: int = DENSE_CANDIDATES,
    bm25_candidates: int = BM25_CANDIDATES,
    fusion_candidates: int = DENSE_CANDIDATES,
    rrf_k: float = RRF_K,
    timings: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    """use_multi_query / use_query_decomposition each accept True / False / "auto":
      - True: always apply upfront (used by evaluate_retrieval.py Configs D/E to
        measure each technique's ceiling in isolation).
      - False: never apply.
      - "auto": on-demand routing, no LLM cost unless genuinely warranted --
          * Query Decomposition gates on query_router.is_complex_question (a
            zero-LLM-cost heuristic) before paying for decompose_query.
          * Multi-Query runs the normal single-query pass first, and only pays for
            generate_query_variants + a second fusion/rerank pass if that pass's
            top-1 reranker score is below MULTI_QUERY_CONFIDENCE_THRESHOLD. Requires
            use_reranker=True -- with reranker off there's no confidence signal to
            gate on, so "auto" behaves like False in that case.
    """
    t0 = time.perf_counter()

    # 0. Query Decomposition: split comparison/multi-part questions into independent
    # sub-questions, each fed into the same RRF fusion below as one more query.
    queries = [question]
    decompose_now = use_query_decomposition is True or (
        use_query_decomposition == "auto" and is_complex_question(question)
    )
    if decompose_now:
        queries.extend(decompose_query(question))
    if use_multi_query is True:
        queries.extend(generate_query_variants(question, n=multi_query_n - 1))
    t_mq = time.perf_counter()
    if timings is not None:
        timings["multi_query_ms"] = (t_mq - t0) * 1000

    # RRF fusion across every query variant's dense list, and (if enabled) BM25 list.
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    for query in queries:
        vector_results = search_chunks(
            question=query,
            course_id=course_id,
            top_k=dense_candidates,
            document_ids=document_ids,
        )
        for rank, chunk in enumerate(vector_results):
            cid = chunk["chunk_id"]
            chunk_map.setdefault(cid, chunk)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))
    t1 = time.perf_counter()
    if timings is not None:
        timings["dense_ms"] = (t1 - t_mq) * 1000

    bm25_model = None
    if not use_bm25:
        if timings is not None:
            timings["bm25_ms"] = 0.0
            timings["fusion_ms"] = 0.0
        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        fused = [chunk_map[cid] for cid in sorted_cids[:fusion_candidates]]
    else:
        bm25_model, _course_chunks = _get_bm25_index(course_id, document_ids)
        t2 = time.perf_counter()
        if timings is not None:
            timings["bm25_ms"] = (t2 - t1) * 1000

        if bm25_model is None:
            # BM25 corpus empty (e.g. course not yet indexed) -- explicit fallback to dense-only,
            # not a silent one: caller can see this via the empty bm25_ms/fusion_ms below.
            if timings is not None:
                timings["fusion_ms"] = 0.0
        else:
            for query in queries:
                bm25_scored = bm25_model.score(query)
                bm25_results = [doc for doc, _score in bm25_scored[:bm25_candidates]]
                for rank, chunk in enumerate(bm25_results):
                    cid = chunk["chunk_id"]
                    chunk_map.setdefault(cid, chunk)
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        fused = [chunk_map[cid] for cid in sorted_cids[:fusion_candidates]]
        if timings is not None:
            timings["fusion_ms"] = (time.perf_counter() - t2) * 1000

    if not use_reranker:
        if timings is not None:
            timings["rerank_ms"] = 0.0
            timings["adaptive_ms"] = 0.0
            timings["total_ms"] = (time.perf_counter() - t0) * 1000
        return fused[:top_k]

    t3 = time.perf_counter()
    reranked = rerank_chunks(question=question, chunks=fused, top_n=top_k)
    if timings is not None:
        timings["rerank_ms"] = (time.perf_counter() - t3) * 1000

    needs_retry = (
        use_multi_query == "auto"
        and reranked
        and reranked[0].get("rerank_score", 0.0) < MULTI_QUERY_CONFIDENCE_THRESHOLD
    )
    if not needs_retry:
        if timings is not None:
            timings["adaptive_ms"] = 0.0
            timings["total_ms"] = (time.perf_counter() - t0) * 1000
        return reranked

    # Multi-Query retry: first pass looked unconfident -- widen recall with LLM
    # paraphrases and re-fuse/re-rerank on top of the candidates already gathered.
    t4 = time.perf_counter()
    variants = generate_query_variants(question, n=multi_query_n - 1)
    _merge_queries_into_fusion(
        variants, course_id, document_ids, dense_candidates, bm25_model,
        bm25_candidates, rrf_k, chunk_map, rrf_scores,
    )
    sorted_cids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    fused = [chunk_map[cid] for cid in sorted_cids[:fusion_candidates]]
    reranked = rerank_chunks(question=question, chunks=fused, top_n=top_k)
    if timings is not None:
        timings["adaptive_ms"] = (time.perf_counter() - t4) * 1000
        timings["total_ms"] = (time.perf_counter() - t0) * 1000
    return reranked


def retrieve_relevant_chunks(
    question: str,
    course_id: int,
    top_k: int = 3,
    document_ids: list[int] | None = None,
    *,
    use_multi_query: bool | str = False,
    use_query_decomposition: bool | str = False,
) -> list[dict[str, object]]:
    return retrieve_ranked(
        question,
        course_id,
        top_k,
        document_ids,
        use_multi_query=use_multi_query,
        use_query_decomposition=use_query_decomposition,
    )
