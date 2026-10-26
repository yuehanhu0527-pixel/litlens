from rank_bm25 import BM25Okapi
from sqlalchemy import select

from app.database import SessionLocal
from app.db_models import Chunk


def tokenize(text: str) -> list[str]:
    return text.lower().split()


def search_chunks_bm25(
    query: str,
    top_k: int = 3,
    document_ids: list[int] | None = None
) -> list[dict]:

    db = SessionLocal()

    try:
        stmt = select(Chunk)

        if document_ids:
            stmt = stmt.where(
                Chunk.document_id.in_(document_ids)
    )

        chunks = db.scalars(stmt).all()

        if not chunks:
            return []

        tokenized_corpus = [
            tokenize(chunk.text)
            for chunk in chunks
        ]

        bm25 = BM25Okapi(tokenized_corpus)

        tokenized_query = tokenize(query)

        scores = bm25.get_scores(tokenized_query)

        scored_chunks = []

        for chunk, score in zip(chunks, scores):
            scored_chunks.append({
                "document_id": chunk.document_id,
                "filename": chunk.document.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "bm25_score": float(score)
            })

        scored_chunks.sort(
            key=lambda item: item["bm25_score"],
            reverse=True
        )

        return scored_chunks[:top_k]

    finally:
        db.close()