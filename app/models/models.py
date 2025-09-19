from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Document(Base):
  __tablename__ = "documents"

  id = Column(Integer, primary_key=True, index=True)
  content_hash = Column(String(64), unique=True, nullable=False)
  title = Column(String(255))
  pages = Column(Integer)
  bytes = Column(Integer)
  status = Column(String(20), default="queued")
  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    ord = Column(Integer)  # Order of chunk in document
    text = Column(Text)
    page_start = Column(Integer)
    page_end = Column(Integer)
    token_count = Column(Integer)

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"))
    vector_data = Column(Text)  # Store as JSON for now
  