from app.hybrid_retrieval import hybrid_search
from app.reranker import rerank_chunks
from app.evidence_utils import make_evidence_id


def retrieve_evidence(
    query: str,
    top_k: int = 5,
    candidate_k: int = 10,
    document_ids: list[int] | None = None
) -> list[dict]:

    candidates = hybrid_search(
    query=query,
    top_k=candidate_k,
    candidate_k=candidate_k,
    document_ids=document_ids
)

    results = rerank_chunks(
        query=query,
        chunks=candidates,
        top_k=top_k
    )

    final_results = []

    for chunk in results:
        final_results.append({
            **chunk,
            "evidence_id": make_evidence_id(chunk)
        })

    return final_results