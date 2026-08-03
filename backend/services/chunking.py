from typing import Callable

from underthesea import sent_tokenize

import numpy as np

from backend.services.embedding_service import embed_texts

DEFAULT_CHUNK_SIZE = 700
DEFAULT_OVERLAP = 100

# Percentile of the adjacent-sentence distance distribution used as the semantic
# breakpoint threshold -- adaptive per page instead of a fixed cosine cutoff,
# following the "percentile threshold" method for semantic chunking. Tuned via
# scripts/sweep_semantic_percentile.py on the 20-question eval set: 85 gave the best
# HitRate/MRR/nDCG among {70,80,85,90,95} (MRR 0.722 vs 0.675 at the untuned 95),
# though it still trails fixed-size chunking on every metric -- see reports/eval/
# percentile_sweep_table.md.
SEMANTIC_BREAKPOINT_PERCENTILE = 85
# Fixed-size chunking always has DEFAULT_OVERLAP chars shared between adjacent
# chunks; semantic grouping has none at all between groups (only inside the
# oversized-group fallback below). Measured via scripts/sweep_semantic_overlap.py
# whether carrying the last N sentences of each group into the next one helps close
# that gap -- it does NOT: overlap=1/2/3 all scored WORSE than overlap=0 (MRR 0.722
# at 0 vs 0.623-0.676 at 1-3). Carrying a trailing sentence from a different
# topic-cluster into the next group dilutes exactly the topic-purity semantic
# chunking is meant to provide, unlike fixed-size chunking which has no topic
# coherence to dilute in the first place. Kept at 0 (disabled) by default; the
# parameter is left in place for anyone who wants to re-test on a different corpus.
SEMANTIC_OVERLAP_SENTENCES = 0
MIN_SENTENCES_FOR_BREAKPOINTS = 4
# Below this, a group is leftover noise (a stray page number fused to one short
# sentence fragment) rather than a usable chunk -- not worth indexing.
MIN_CHUNK_CHARS = 20


def split_into_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    # underthesea's sent_tokenize is Vietnamese-aware -- unlike a plain regex on
    # ". ! ?", it doesn't treat abbreviations/numbered headings ("2CD3.",
    # "Mã số...") as sentence ends nearly as often, which matters because a bad
    # split point becomes a bad semantic-chunk breakpoint downstream.
    return [s.strip() for s in sent_tokenize(text) if s.strip()]


def create_semantic_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    percentile: float = SEMANTIC_BREAKPOINT_PERCENTILE,
    overlap_sentences: int = SEMANTIC_OVERLAP_SENTENCES,
) -> list[str]:
    """Group sentences by topic continuity instead of cutting at a fixed offset.

    Adjacent sentences whose embeddings are more dissimilar than the given
    percentile of the page's own distance distribution start a new group --
    this keeps a subject and its predicate/action together instead of
    splitting them across two chunks. Any resulting group still larger than
    chunk_size falls back to split_text_with_overlap, so no chunk ever exceeds
    the size budget the rest of the pipeline (embedding, prompt context) expects.
    """
    sentences = split_into_sentences(text)
    if not sentences:
        return split_text_with_overlap(text, chunk_size=chunk_size, overlap=overlap)

    if len(sentences) < MIN_SENTENCES_FOR_BREAKPOINTS:
        groups = [sentences]
    else:
        vectors = np.array(embed_texts(sentences))
        # Embeddings are already normalized (embed_texts), so dot product == cosine similarity.
        similarities = np.sum(vectors[:-1] * vectors[1:], axis=1)
        distances = 1.0 - similarities
        breakpoint_distance = float(np.percentile(distances, percentile))

        groups = []
        current = [sentences[0]]
        for i, dist in enumerate(distances):
            if dist >= breakpoint_distance:
                groups.append(current)
                current = [sentences[i + 1]]
            else:
                current.append(sentences[i + 1])
        groups.append(current)

    overlapped_groups: list[list[str]] = []
    for i, group in enumerate(groups):
        if i == 0 or overlap_sentences <= 0:
            overlapped_groups.append(group)
        else:
            carry = groups[i - 1][-overlap_sentences:]
            overlapped_groups.append(carry + group)

    final_chunks: list[str] = []
    for group in overlapped_groups:
        joined = " ".join(group)
        if len(joined) <= chunk_size:
            final_chunks.append(joined)
        else:
            final_chunks.extend(split_text_with_overlap(joined, chunk_size=chunk_size, overlap=overlap))
    return [c for c in final_chunks if len(c) >= MIN_CHUNK_CHARS]


def split_text_with_overlap(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def create_chunks(
    document_id: int,
    course_id: int,
    document_name: str,
    pages: list[dict[str, str | int]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    percentile: float = SEMANTIC_BREAKPOINT_PERCENTILE,
    overlap_sentences: int = SEMANTIC_OVERLAP_SENTENCES,
    use_semantic: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict[str, str | int]]:
    all_chunks: list[dict[str, str | int]] = []

    for page_num, page in enumerate(pages, start=1):
        if progress_callback is not None:
            progress_callback(page_num, len(pages))
        page_number = int(page["page"])
        page_text = str(page["text"])
        if use_semantic:
            page_chunks = create_semantic_chunks(
                page_text,
                chunk_size=chunk_size,
                overlap=overlap,
                percentile=percentile,
                overlap_sentences=overlap_sentences,
            )
        else:
            page_chunks = split_text_with_overlap(page_text, chunk_size=chunk_size, overlap=overlap)

        for index, chunk_text in enumerate(page_chunks):
            chunk_id = f"course{course_id}_doc{document_id}_p{page_number}_c{index}"
            all_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "course_id": course_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": page_number,
                    "chunk_index": index,
                    "text": chunk_text,
                }
            )

    return all_chunks
