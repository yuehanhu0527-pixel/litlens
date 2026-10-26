from app.retrieval_pipeline import retrieve_evidence


def retrieve_evidence_per_document(
    query: str,
    document_ids: list[int],
    top_k_per_document: int = 2
) -> dict[int, list[dict]]:

    results_by_document = {}

    for document_id in document_ids:

        evidence = retrieve_evidence(
        query=query,
        top_k=top_k_per_document,
        document_ids=[document_id]
    )

        results_by_document[document_id] = evidence

    return results_by_document