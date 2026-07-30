import chromadb

from backend.config import get_settings
from backend.services.embedding_service import embed_text, embed_texts


COLLECTION_NAME = "learning_documents"


client = chromadb.PersistentClient(path=get_settings().vector_db_path)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def add_chunks_to_vector_store(chunks: list[dict[str, object]]) -> int:
    if not chunks:
        return 0

    texts = [str(chunk["text"]) for chunk in chunks]
    embeddings = embed_texts(texts)
    ids = [str(chunk["chunk_id"]) for chunk in chunks]
    metadatas = [
        {
            "course_id": str(chunk["course_id"]),
            "document_id": str(chunk["document_id"]),
            "document_name": str(chunk["document_name"]),
            "page": int(chunk["page"]),
            "chunk_index": int(chunk["chunk_index"]),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(chunks)


def _build_where(course_id: int, document_ids: list[int] | None) -> dict[str, object]:
    course_filter = {"course_id": str(course_id)}
    if not document_ids:
        return course_filter
    if len(document_ids) == 1:
        doc_filter = {"document_id": str(document_ids[0])}
    else:
        doc_filter = {"document_id": {"$in": [str(d) for d in document_ids]}}
    return {"$and": [course_filter, doc_filter]}


def get_collection_count() -> int:
    return collection.count()


def search_chunks(
    question: str,
    course_id: int,
    top_k: int = 5,
    document_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    query_embedding = embed_text(question)

    where = _build_where(course_id, document_ids)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    output: list[dict[str, object]] = []
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, chunk_id in enumerate(ids):
        output.append(
            {
                "chunk_id": chunk_id,
                "text": documents[index],
                "metadata": metadatas[index],
                "distance": distances[index],
            }
        )

    return output


def get_all_chunks_for_course(
    course_id: int,
    document_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    where = _build_where(course_id, document_ids)

    res = collection.get(where=where, include=["documents", "metadatas"])
    
    output: list[dict[str, object]] = []
    if res and "ids" in res:
        ids = res["ids"]
        documents = res.get("documents", [])
        metadatas = res.get("metadatas", [])
        for idx, cid in enumerate(ids):
            output.append({
                "chunk_id": cid,
                "text": documents[idx],
                "metadata": metadatas[idx],
            })
    return output


def save_chunks(collection_name: str, chunks: list[str]) -> None:
    raise NotImplementedError("Use add_chunks_to_vector_store for metadata-aware chunk indexing.")
