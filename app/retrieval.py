import numpy as np

from app.embeddings import embed_text


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    a = np.array(vector_a)
    b = np.array(vector_b)

    similarity = np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

    return float(similarity)


def search_chunks(
    query: str,
    embedded_chunks: list[dict],
    top_k: int = 5
) -> list[dict]:

    query_embedding = embed_text(query)

    scored_chunks = []

    for chunk in embedded_chunks:
        score = cosine_similarity(
            query_embedding,
            chunk["embedding"]
        )

        scored_chunks.append({
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
            "score": score
        })

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return scored_chunks[:top_k]

