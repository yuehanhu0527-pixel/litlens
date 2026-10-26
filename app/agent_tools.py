from langchain_core.tools import tool

from app.retrieval_pipeline import retrieve_evidence
from sqlalchemy import select
from langchain_core.tools import tool

from app.database import SessionLocal
from app.db_models import Chunk, Document
from app.retrieval_pipeline import retrieve_evidence


@tool
def search_document(
    document_id: int,
    query: str,
    top_k: int = 3
) -> list[dict]:
    """
    Search for relevant evidence inside one research document.

    Use this tool when evidence from a specific document
    needs to be found or improved.
    """

    evidence = retrieve_evidence(
        query=query,
        top_k=top_k,
        document_ids=[document_id]
    )

    return evidence

@tool
def get_adjacent_context(
    document_id: int,
    page_number: int,
    chunk_index: int,
    window: int = 1
) -> list[dict]:
    """
    Read nearby chunks around a known evidence chunk
    inside the same research document and page.

    Use this tool when an evidence chunk is relevant
    but its surrounding context is needed.
    """

    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # Get document information
        # ----------------------------------------------------

        document = db.execute(
            select(Document).where(
                Document.id == document_id
            )
        ).scalar_one_or_none()

        filename = (
            document.filename
            if document
            else f"document_{document_id}"
        )


        # ----------------------------------------------------
        # Find nearby chunks
        # ----------------------------------------------------

        start_index = max(
            0,
            chunk_index - window
        )

        end_index = (
            chunk_index + window
        )

        stmt = (
            select(Chunk)
            .where(
                Chunk.document_id == document_id,
                Chunk.page_number == page_number,
                Chunk.chunk_index >= start_index,
                Chunk.chunk_index <= end_index
            )
            .order_by(
                Chunk.chunk_index
            )
        )

        chunks = db.execute(
            stmt
        ).scalars().all()


        # ----------------------------------------------------
        # Build evidence objects
        # ----------------------------------------------------

        results = []

        for chunk in chunks:

            results.append({
                "document_id": chunk.document_id,
                "filename": filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "evidence_id": (
                    f"doc_{chunk.document_id}_"
                    f"page_{chunk.page_number}_"
                    f"chunk_{chunk.chunk_index}"
                )
            })

        return results

    finally:
        db.close()