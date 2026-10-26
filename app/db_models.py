from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(
        String,
        nullable=True,
        index=True
    )


    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    chunks = relationship(
        "Chunk",
        back_populates='document',
        cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    text = Column(Text, nullable=False)

    embedding = Column(Vector(384))

    document = relationship(
        "Document",
        back_populates="chunks"
        )