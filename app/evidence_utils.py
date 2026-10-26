def make_evidence_id(chunk: dict) -> str:
    return (
        f"doc_{chunk['document_id']}_"
        f"page_{chunk['page_number']}_"
        f"chunk_{chunk['chunk_index']}"
    )