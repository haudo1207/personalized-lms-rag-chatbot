

from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DB_PATH = "vector_store"
COLLECTION_NAME = "learning_documents"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    embedding = get_embedding_model().encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    embeddings = get_embedding_model().encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
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


def search_chunks(question: str, course_id: int, top_k: int = 5) -> list[dict[str, object]]:
    query_embedding = embed_text(question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"course_id": str(course_id)},
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

