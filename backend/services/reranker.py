import numpy as np
from backend.services.embedding_service import embed_text
from backend.services import vector_store

def rerank_chunks(question: str, chunks: list[dict], top_n: int = 3) -> list[dict]:
    if not chunks:
        return []

    # Get the query embedding
    query_emb = np.array(embed_text(question))

    # Retrieve pre-computed embeddings for the chunks from ChromaDB
    chunk_ids = [str(chunk["chunk_id"]) for chunk in chunks]
    db_res = vector_store.collection.get(ids=chunk_ids, include=["embeddings", "documents", "metadatas"])
    
    # Map from ID to embedding
    id_to_emb = {}
    if db_res and "ids" in db_res and "embeddings" in db_res:
        for idx, cid in enumerate(db_res["ids"]):
            emb = db_res["embeddings"][idx]
            if emb is not None:
                id_to_emb[cid] = np.array(emb)
                
    # Calculate cosine similarity (dot product of normalized vectors)
    scored_chunks = []
    for chunk in chunks:
        cid = str(chunk["chunk_id"])
        emb = id_to_emb.get(cid)
        if emb is None:
            # Fallback to computing embedding on the fly if not found in db
            emb = np.array(embed_text(str(chunk.get("text", ""))))
            
        # Dot product
        score = float(np.dot(query_emb, emb))
        chunk_copy = dict(chunk)
        chunk_copy["distance"] = 1.0 - score  # update distance for metadata/reporting
        chunk_copy["rerank_score"] = score
        scored_chunks.append((chunk_copy, score))
        
    # Sort by score descending
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    # Return top_n chunks
    return [item[0] for item in scored_chunks[:top_n]]
