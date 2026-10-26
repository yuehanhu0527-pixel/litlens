import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from app.pdf_parser import extract_pages_from_pdf
from app.chunker import chunk_pages
from app.embeddings import embed_chunks
from app.models import AskRequest, VerifyRequest
from app.llm import answer_with_evidence, verify_claim_with_evidence
from app.database import SessionLocal
from app.db_models import Document, Chunk
from app.db_retrieval import search_chunks_db
from sqlalchemy import select, func
from fastapi import HTTPException
from app.bm25_retrieval import search_chunks_bm25
from app.hybrid_retrieval import hybrid_search
from app.reranker import rerank_chunks
from app.retrieval_pipeline import retrieve_evidence
from app.models import AskRequest, VerifyRequest, ExploreRequest
from app.multi_doc_retrieval import retrieve_evidence_per_document
from app.explore import compare_documents_with_evidence
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.explore_agent import explore_agent_graph
from datetime import datetime, timedelta, timezone


MAX_DOCUMENTS_PER_SESSION = 10
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
WORKSPACE_TTL_HOURS = 24


def cleanup_expired_documents():
    cutoff_time = (
        datetime.now(timezone.utc)
        - timedelta(hours=WORKSPACE_TTL_HOURS)
    )

    db = SessionLocal()

    try:
        expired_documents = db.scalars(
            select(Document).where(
                Document.session_id.is_not(None),
                Document.created_at < cutoff_time
            )
        ).all()

        for document in expired_documents:

            file_path = os.path.join(
                "data",
                document.session_id,
                document.filename
            )

            if os.path.exists(file_path):
                os.remove(file_path)

            db.delete(document)

        db.commit()

    finally:
        db.close()

app = FastAPI(
    title="LitLens",
    description="An Evidence-Grounded Reading Companion for Research Papers"
)
app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse("frontend/index.html")

@app.get("/")
def root():
    return {
        "message": "LitLens API is running"
    }


    
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_session_id: str = Header(..., alias="X-Session-ID")
):

    db = SessionLocal()

    try:
        # ----------------------------------------------------
        # 1. Check document limit BEFORE expensive processing
        # ----------------------------------------------------

        document_count = db.scalar(
            select(func.count(Document.id)).where(
                Document.session_id == x_session_id
            )
        )

        if document_count >= MAX_DOCUMENTS_PER_SESSION:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This workspace supports up to "
                    f"{MAX_DOCUMENTS_PER_SESSION} documents."
                )
            )


        # ----------------------------------------------------
        # 2. Check duplicate filename
        # ----------------------------------------------------

        existing_document = db.scalar(
            select(Document).where(
                Document.session_id == x_session_id,
                Document.filename == file.filename
            )
        )

        if existing_document is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A document with this filename "
                    "already exists."
                )
            )


        # ----------------------------------------------------
        # 3. Save and process PDF
        # ----------------------------------------------------

        session_dir = os.path.join(
            "data",
            x_session_id
        )

        os.makedirs(
            session_dir,
            exist_ok=True
        )

        file_path = os.path.join(
            session_dir,
            file.filename
        )

        contents = await file.read()

        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"PDF must be {MAX_FILE_SIZE_MB} MB or smaller."
                )
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        pages = extract_pages_from_pdf(
            file_path
        )

        chunks = chunk_pages(
            pages
        )

        embedded_chunks = embed_chunks(
            chunks
        )


        # ----------------------------------------------------
        # 4. Save document
        # ----------------------------------------------------

        document = Document(
            session_id=x_session_id,
            filename=file.filename,
            title=file.filename
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        document_id = document.id


        # ----------------------------------------------------
        # 5. Save chunks
        # ----------------------------------------------------

        for chunk in embedded_chunks:

            db_chunk = Chunk(
                document_id=document_id,
                page_number=chunk["page_number"],
                chunk_index=chunk["chunk_index"],
                text=chunk["text"],
                embedding=chunk["embedding"]
            )

            db.add(db_chunk)

        db.commit()


        return {
            "document_id": document_id,
            "filename": file.filename,
            "total_pages": len(pages),
            "total_chunks": len(chunks)
        }

    finally:
        db.close()


@app.get("/search")
def search(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid"
):

    if mode == "vector":
        results = search_chunks_db(
            query=query,
            top_k=top_k
        )

    elif mode == "bm25":
        results = search_chunks_bm25(
            query=query,
            top_k=top_k
        )

    elif mode == "hybrid":
        results = hybrid_search(
            query=query,
            top_k=top_k
        )

    elif mode == "hybrid_rerank":

        candidates = hybrid_search(
            query=query,
            top_k=10,
            candidate_k=10
        )

        results = rerank_chunks(
            query=query,
            chunks=candidates,
            top_k=top_k
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="mode must be 'vector', 'bm25', or 'hybrid'"
        )

    return {
        "query": query,
        "mode": mode,
        "results": results
    }

def resolve_document_scope(
    document_ids: list[int] | None,
    x_session_id: str
) -> list[int]:

    db = SessionLocal()

    try:
        # All papers in this workspace
        if document_ids is None:

            owned_ids = list(
                db.scalars(
                    select(Document.id).where(
                        Document.session_id == x_session_id
                    )
                ).all()
            )

            if not owned_ids:
                raise HTTPException(
                    status_code=400,
                    detail="No documents available in this workspace."
                )

            return owned_ids

        # Explicitly selected papers
        if len(document_ids) == 0:
            raise HTTPException(
                status_code=400,
                detail="Select at least one document."
            )

        owned_ids = list(
            db.scalars(
                select(Document.id).where(
                    Document.session_id == x_session_id,
                    Document.id.in_(document_ids)
                )
            ).all()
        )

        if set(owned_ids) != set(document_ids):
            raise HTTPException(
                status_code=404,
                detail=(
                    "One or more documents were not found "
                    "in this workspace."
                )
            )

        return document_ids

    finally:
        db.close()


@app.post("/ask")
def ask(
    request: AskRequest,
    x_session_id: str = Header(
        ...,
        alias="X-Session-ID"
    )
):

    document_ids = resolve_document_scope(
        request.document_ids,
        x_session_id
    )

    evidence_chunks = retrieve_evidence(
        query=request.question,
        top_k=request.top_k,
        document_ids=document_ids
    )

    result = answer_with_evidence(
        question=request.question,
        evidence_chunks=evidence_chunks
    )

    return {
        **result,
        "evidence": evidence_chunks
    }
@app.post("/verify")
def verify(
    request: VerifyRequest,
    x_session_id: str = Header(
        ...,
        alias="X-Session-ID"
    )
):

    document_ids = resolve_document_scope(
        request.document_ids,
        x_session_id
    )

    evidence_chunks = retrieve_evidence(
        query=request.claim,
        top_k=request.top_k,
        document_ids=document_ids
    )

    result = verify_claim_with_evidence(
        claim=request.claim,
        evidence_chunks=evidence_chunks
    )

    return {
        "claim": request.claim,
        **result,
        "evidence": evidence_chunks
    }

@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    x_session_id: str = Header(
        ...,
        alias="X-Session-ID"
    )
):

    db = SessionLocal()

    try:
        document = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.session_id == x_session_id
            )
        )

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found in this workspace."
            )

        filename = document.filename

        file_path = os.path.join(
            "data",
            x_session_id,
            filename
        )

        # Delete database record
        # Related chunks are deleted by cascade.
        db.delete(document)
        db.commit()

        # Delete the original PDF from disk.
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "message": "Document deleted.",
            "document_id": document_id
        }

    finally:
        db.close()

@app.get("/documents")
def list_documents(
    x_session_id: str = Header(
        ...,
        alias="X-Session-ID"
    )
):

    cleanup_expired_documents()

    db = SessionLocal()

    try:
        documents = db.scalars(
            select(Document)
            .where(
                Document.session_id == x_session_id
            )
            .order_by(Document.id)
        ).all()

        results = []

        for document in documents:
            results.append({
                "document_id": document.id,
                "filename": document.filename,
                "title": document.title,
                "created_at": document.created_at
            })

        return results

    finally:
        db.close()

@app.post("/explore")
def explore(
    request: ExploreRequest,
    x_session_id: str = Header(
        ...,
        alias="X-Session-ID"
    )
):

    if len(request.document_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="Explore requires at least two documents."
        )

    document_ids = resolve_document_scope(
        request.document_ids,
        x_session_id
    )

    initial_state = {
        "question": request.question,
        "document_ids": document_ids,
        "top_k_per_document": request.top_k_per_document
    }

    final_state = explore_agent_graph.invoke(
        initial_state
    )

    return final_state["result"]