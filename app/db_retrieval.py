from sqlalchemy import select

from app.database import SessionLocal
from app.db_models import Chunk
from app.embeddings import embed_text


def search_chunks_db(
    query: str,
    top_k: int = 3,
    document_ids: list[int] | None = None
) -> list[dict]:

    query_embedding = embed_text(query)

    db = SessionLocal()

    try:
        stmt = select(Chunk)

        if document_ids:
            stmt = stmt.where(
                Chunk.document_id.in_(document_ids)
            )

        stmt = (
            stmt
            .order_by(
                Chunk.embedding.cosine_distance(query_embedding)
            )
            .limit(top_k)
        )

        chunks = db.scalars(stmt).all()

        results = []

        for chunk in chunks:
            results.append({
                "document_id": chunk.document_id,
                "filename": chunk.document.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text
            })

        return results

    finally:
        db.close()