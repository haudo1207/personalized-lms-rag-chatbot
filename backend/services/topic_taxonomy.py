"""Course-aware topic classification.

Labels are generated once per course from the course's OWN indexed content,
by clustering the full chunk-embedding set (KMeans) and asking the LLM for a
short label per cluster -- not by sampling only the introduction.

That distinction matters at real textbook scale: an earlier version sampled
positionally (first N chunks of each document, or even evenly-spaced chunks
across each document) and it produced generic overview labels ("Tổng quan
CSDL", "Đặc tính CSDL") that scored well under the classification threshold
against real student questions ("Khóa chính là gì?", "INNER JOIN khác LEFT
JOIN như thế nào?") -- confirmed empirically against a real 583-chunk course.
Clustering guarantees topical diversity by construction: a chunk about JOIN
forms a different cluster than one about normalization even if they sit far
apart in the document, whereas positional sampling only catches a concept if
it happens to land in the sampled slice.
"""

from __future__ import annotations

import json
import re

import numpy as np
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session

from backend.models.course_topic import CourseTopic
from backend.services.embedding_service import embed_text
from backend.services.llm_service import generate_answer
from backend.services.vector_store import get_chunk_embeddings_for_course

MIN_LABELS = 3
MAX_LABELS = 8
# A fixed cluster count doesn't generalize: 7-8 clusters is reasonable for a
# 500+ chunk textbook, but the same number over a 25-chunk slide deck would
# force ~3 chunks per cluster -- clusters that thin aren't distinct topics,
# they're noise, and produce redundant near-duplicate labels ("JOIN cơ bản",
# "Ví dụ JOIN"). Cluster count instead scales with how much content there
# actually is, floored/capped to keep it in the 3-8 label range regardless.
CHUNKS_PER_LABEL = 15  # like CLASSIFICATION_THRESHOLD below: a reasoned default, not measured against labeled data
EXCERPT_CHARS = 400
# Not calibrated against a labeled dataset (there is no fixed set of
# question -> true-topic pairs to calibrate against across arbitrary
# courses, unlike the retrieval eval harness). Chosen from the typical
# behavior of this sentence-embedding model on related-but-not-identical
# short Vietnamese text: a reasoned default, not a measured one -- flagged
# explicitly rather than presented as tuned.
CLASSIFICATION_THRESHOLD = 0.35
FALLBACK_TOPIC = "Khác"


def _choose_cluster_count(n_chunks: int) -> int:
    if n_chunks <= 1:
        return 1
    target = max(MIN_LABELS, n_chunks // CHUNKS_PER_LABEL)
    return min(target, MAX_LABELS, n_chunks)


def _cluster_representative_chunks(course_id: int) -> list[str]:
    chunks = get_chunk_embeddings_for_course(course_id)
    if not chunks:
        return []

    vectors = np.array([c["embedding"] for c in chunks])
    k = _choose_cluster_count(len(chunks))
    if k < 2:
        return [str(chunks[0]["text"])[:EXCERPT_CHARS]]

    labels = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(vectors)
    centroids = np.zeros((k, vectors.shape[1]))
    for cluster_id in range(k):
        centroids[cluster_id] = vectors[labels == cluster_id].mean(axis=0)

    representatives: list[str] = []
    for cluster_id in range(k):
        member_indices = np.where(labels == cluster_id)[0]
        member_vectors = vectors[member_indices]
        distances = np.linalg.norm(member_vectors - centroids[cluster_id], axis=1)
        closest = member_indices[int(np.argmin(distances))]
        representatives.append(str(chunks[closest]["text"])[:EXCERPT_CHARS])
    return representatives


def _extract_labels(text: str, expected_count: int) -> list[str]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        array_match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
        if not array_match:
            return []
        parsed = json.loads(array_match.group(0))
    if not isinstance(parsed, list):
        return []
    labels = [str(label).strip() for label in parsed if str(label).strip()]
    return labels[:expected_count]


def generate_taxonomy_for_course(course_id: int, db: Session) -> list[CourseTopic]:
    """Generates and persists this course's topic labels. One LLM call, made
    once (the caller is responsible for checking a taxonomy doesn't already
    exist -- see ensure_taxonomy_for_course)."""
    excerpts = _cluster_representative_chunks(course_id)
    if not excerpts:
        return []

    numbered_excerpts = "\n\n".join(f"[{i + 1}] {excerpt}" for i, excerpt in enumerate(excerpts))
    prompt = f"""Dưới đây là {len(excerpts)} đoạn trích, mỗi đoạn thuộc một chủ đề khác nhau trong tài liệu
của một môn học. Với MỖI đoạn, hãy đặt một nhãn chủ đề ngắn (2-5 từ, tiếng Việt) mô tả đúng nội dung
đoạn đó -- dùng để phân loại câu hỏi của sinh viên. Không suy diễn ngoài nội dung đoạn trích.

{numbered_excerpts}

Trả về một JSON array gồm đúng {len(excerpts)} chuỗi nhãn chủ đề, theo ĐÚNG thứ tự đoạn trích trên,
không thêm giải thích ngoài JSON. Ví dụ định dạng: ["Nhãn 1", "Nhãn 2", ...]"""

    response = generate_answer(prompt)
    labels = _extract_labels(response, len(excerpts))
    if not labels:
        return []

    seen: set[str] = set()
    rows: list[CourseTopic] = []
    for label in labels:
        if label in seen:
            continue  # two clusters occasionally get the same label wording -- keep the label once
        seen.add(label)
        rows.append(CourseTopic(course_id=course_id, label=label, embedding=json.dumps(embed_text(label))))

    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def ensure_taxonomy_for_course(course_id: int, db: Session) -> None:
    """Idempotent trigger point: call after a document finishes indexing.
    No-ops if this course already has a taxonomy -- taxonomy generation is
    a one-time event per course, not regenerated on every new document."""
    existing = db.query(CourseTopic).filter(CourseTopic.course_id == course_id).first()
    if existing:
        return
    generate_taxonomy_for_course(course_id, db)


def classify_topic(question: str, course_id: int, db: Session) -> str:
    """Course-aware, zero-LLM-per-question classification: embed the question
    once, compare against this course's own topic labels by cosine similarity.
    Falls back to "Khác" if the course has no taxonomy yet (not indexed, or
    generation failed) -- never pretends a match that isn't there."""
    topics = db.query(CourseTopic).filter(CourseTopic.course_id == course_id).all()
    if not topics:
        return FALLBACK_TOPIC

    question_vector = np.array(embed_text(question))
    label_vectors = np.array([json.loads(t.embedding) for t in topics])
    # Both sides are already L2-normalized (embed_text), so the dot product
    # alone equals cosine similarity -- same trick chunking.py uses.
    scores = label_vectors @ question_vector

    best_index = int(np.argmax(scores))
    if scores[best_index] < CLASSIFICATION_THRESHOLD:
        return FALLBACK_TOPIC
    return topics[best_index].label
