from sentence_transformers import CrossEncoder


reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5
) -> list[dict]:

    if not chunks:
        return []

    pairs = [
        [query, chunk["text"]]
        for chunk in chunks
    ]

    scores = reranker.predict(pairs)

    reranked = []

    for chunk, score in zip(chunks, scores):
        reranked.append({
            **chunk,
            "rerank_score": float(score)
        })

    reranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return reranked[:top_k]