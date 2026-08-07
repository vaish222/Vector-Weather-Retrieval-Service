"""
Ingest Weather Embeddings Script

Reads unembedded weather documents from Lakebase, chunks narrative text,
generates embeddings using sentence-transformers, and writes to weather_embeddings table.

Usage:
    python ingest_weather_embeddings.py
"""

import json
import logging
import sys
from datetime import datetime

# Add parent directory to path so we can import local modules
sys.path.insert(0, "/Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service")

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from sentence_transformers import SentenceTransformer

import lakebase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chunking config
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Embedding model (384-dim)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def ensure_tables():
    """Create weather_documents and weather_embeddings tables if they don\'t exist."""
    
    # Create weather_documents table
    lakebase.run_write("""
        CREATE TABLE IF NOT EXISTS weather_documents (
            id TEXT PRIMARY KEY,
            location TEXT,
            source_type TEXT,
            headline TEXT,
            event TEXT,
            severity TEXT,
            urgency TEXT,
            narrative_text TEXT NOT NULL,
            issued_at TIMESTAMPTZ,
            effective_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            temperature NUMERIC,
            temperature_unit TEXT,
            wind_speed TEXT,
            wind_direction TEXT,
            payload JSONB,
            synced_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            embedded BOOLEAN DEFAULT FALSE
        )
    """)
    logger.info("✓ weather_documents table ready")
    
    # Enable pgvector extension
    lakebase.run_write("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create weather_embeddings table
    lakebase.run_write("""
        CREATE TABLE IF NOT EXISTS weather_embeddings (
            id SERIAL PRIMARY KEY,
            document_id TEXT NOT NULL REFERENCES weather_documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding vector(384),
            model_name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(document_id, chunk_index)
        )
    """)
    logger.info("✓ weather_embeddings table ready")
    
    # Create HNSW index for fast vector search
    try:
        lakebase.run_write("""
            CREATE INDEX IF NOT EXISTS weather_embeddings_hnsw_idx 
            ON weather_embeddings 
            USING hnsw (embedding vector_cosine_ops)
        """)
        logger.info("✓ HNSW index created")
    except Exception as e:
        logger.warning(f"HNSW index creation skipped: {e}")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def process_documents(model: SentenceTransformer, batch_size: int = 50):
    """Read unembedded documents, chunk, embed, and write to weather_embeddings."""
    
    # Fetch unembedded documents
    docs = lakebase.run_query("""
        SELECT id, narrative_text 
        FROM weather_documents 
        WHERE embedded = FALSE OR embedded IS NULL
        ORDER BY synced_at DESC
    """)
    
    if not docs:
        logger.info("No unembedded documents found")
        return
    
    logger.info(f"Processing {len(docs)} unembedded documents")
    
    total_chunks = 0
    
    with lakebase.get_connection() as conn:
        with conn.cursor() as cur:
            for doc in docs:
                doc_id = doc["id"]
                text = doc["narrative_text"]
                
                # Chunk the narrative text
                chunks = chunk_text(text)
                
                # Generate embeddings for all chunks
                embeddings = model.encode(chunks, show_progress_bar=False)
                
                # Prepare batch insert data
                insert_data = [
                    (doc_id, idx, chunk, embedding.tolist(), MODEL_NAME)
                    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
                
                # Batch insert embeddings
                execute_values(
                    cur,
                    """
                    INSERT INTO weather_embeddings 
                        (document_id, chunk_index, chunk_text, embedding, model_name)
                    VALUES %s
                    ON CONFLICT (document_id, chunk_index) DO UPDATE
                    SET chunk_text = EXCLUDED.chunk_text,
                        embedding = EXCLUDED.embedding,
                        model_name = EXCLUDED.model_name,
                        created_at = now()
                    """,
                    insert_data,
                    template="(%s, %s, %s, %s::vector, %s)"
                )
                
                # Mark document as embedded
                cur.execute(
                    "UPDATE weather_documents SET embedded = TRUE WHERE id = %s",
                    (doc_id,)
                )
                
                total_chunks += len(chunks)
                
                if total_chunks % 100 == 0:
                    logger.info(f"Processed {total_chunks} chunks...")
            
            conn.commit()
    
    logger.info(f"✓ Processed {len(docs)} documents → {total_chunks} chunks")


def main():
    """Main ingestion pipeline."""
    logger.info("Starting weather embeddings ingestion...")
    
    # Ensure tables exist
    ensure_tables()
    
    # Load embedding model
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info("✓ Model loaded")
    
    # Process documents
    process_documents(model)
    
    logger.info("✓ Ingestion complete!")


if __name__ == "__main__":
    main()
