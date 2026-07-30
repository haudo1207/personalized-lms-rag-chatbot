import re

import numpy as np

from backend.services.embedding_service import embed_texts

DEFAULT_CHUNK_SIZE = 700
DEFAULT_OVERLAP = 100

# Percentile of the adjacent-sentence distance distribution used as the semantic
# breakpoint threshold -- adaptive per page instead of a fixed cosine cutoff,
# following the "percentile threshold" method for semantic chunking.
SEMANTIC_BREAKPOINT_PERCENTILE = 95
MIN_SENTENCES_FOR_BREAKPOINTS = 4
# Below this, a group is leftover noise (a stray page number fused to one short
# sentence fragment) rather than a usable chunk -- not worth indexing.
MIN_CHUNK_CHARS = 20

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_into_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def create_semantic_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    percentile: float = SEMANTIC_BREAKPOINT_PERCENTILE,
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
        groups = [" ".join(sentences)]
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
                groups.append(" ".join(current))
                current = [sentences[i + 1]]
            else:
                current.append(sentences[i + 1])
        groups.append(" ".join(current))

    final_chunks: list[str] = []
    for group in groups:
        if len(group) <= chunk_size:
            final_chunks.append(group)
        else:
            final_chunks.extend(split_text_with_overlap(group, chunk_size=chunk_size, overlap=overlap))
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
) -> list[dict[str, str | int]]:
    all_chunks: list[dict[str, str | int]] = []

    for page in pages:
        page_number = int(page["page"])
        page_text = str(page["text"])
        page_chunks = create_semantic_chunks(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

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


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    return split_text_with_overlap(text, chunk_size=chunk_size, overlap=overlap)
