from sentence_transformers import CrossEncoder


reranker = None


def get_reranker():
    global reranker

    if reranker is None:
        reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    return reranker


def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5
) -> list[dict]:

    if not chunks:
        return []

    model = get_reranker()

    pairs = [
        [query, chunk["text"]]
        for chunk in chunks
    ]

    scores = model.predict(pairs)

    reranked = []

    for chunk, score in zip(
        chunks,
        scores
    ):
        reranked.append({
            **chunk,
            "rerank_score": float(score)
        })

    reranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return reranked[:top_k]