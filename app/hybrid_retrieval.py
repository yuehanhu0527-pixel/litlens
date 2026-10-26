from app.bm25_retrieval import search_chunks_bm25
from app.db_retrieval import search_chunks_db


def make_chunk_key(chunk: dict) -> tuple:
    return (
        chunk["document_id"],
        chunk["page_number"],
        chunk["chunk_index"]
    )


def hybrid_search(
    query: str,
    top_k: int = 5,
    candidate_k: int = 10,
    rrf_k: int = 60,
    document_ids: list[int] | None = None
) -> list[dict]:

    bm25_results = search_chunks_bm25(
    query=query,
    top_k=candidate_k,
    document_ids=document_ids
)

    vector_results = search_chunks_db(
    query=query,
    top_k=candidate_k,
    document_ids=document_ids
)

    fused = {}

    for rank, chunk in enumerate(bm25_results, start=1):
        key = make_chunk_key(chunk)

        if key not in fused:
            fused[key] = {
                **chunk,
                "rrf_score": 0.0
            }

        fused[key]["rrf_score"] += 1 / (rrf_k + rank)

    for rank, chunk in enumerate(vector_results, start=1):
        key = make_chunk_key(chunk)

        if key not in fused:
            fused[key] = {
                **chunk,
                "rrf_score": 0.0
            }

        fused[key]["rrf_score"] += 1 / (rrf_k + rank)

    results = list(fused.values())

    results.sort(
        key=lambda item: item["rrf_score"],
        reverse=True
    )

    return results[:top_k]