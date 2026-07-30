from functools import lru_cache

from sentence_transformers import CrossEncoder

# Multilingual MS MARCO cross-encoder (mMARCO training data includes Vietnamese).
# Scores (question, passage) pairs jointly, unlike the dense retriever which scores
# them independently -- an actual second, complementary relevance signal instead of
# re-sorting by the same embedding space already used for dense search.
RERANKER_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


@lru_cache(maxsize=1)
def get_reranker_model() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL_NAME)


def rerank_chunks(question: str, chunks: list[dict], top_n: int = 3) -> list[dict]:
    if not chunks:
        return []

    pairs = [(question, str(chunk.get("text", ""))) for chunk in chunks]
    scores = get_reranker_model().predict(pairs)

    scored_chunks = []
    for chunk, score in zip(chunks, scores):
        chunk_copy = dict(chunk)
        chunk_copy["rerank_score"] = float(score)
        scored_chunks.append((chunk_copy, float(score)))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in scored_chunks[:top_n]]
