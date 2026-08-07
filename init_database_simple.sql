
-- ============================================================================
-- Weather Retrieval Service - Database Initialization Script
-- ============================================================================
-- Run this script using any PostgreSQL client (psql, DBeaver, pgAdmin, etc.)
-- Or from your local machine if you have psql installed
--
-- Usage:
--   psql "<your-connection-string>" < init_database_simple.sql
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create weather_documents table
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
);

-- Create indexes on weather_documents
CREATE INDEX IF NOT EXISTS idx_weather_docs_location ON weather_documents(location);
CREATE INDEX IF NOT EXISTS idx_weather_docs_source_type ON weather_documents(source_type);
CREATE INDEX IF NOT EXISTS idx_weather_docs_synced_at ON weather_documents(synced_at DESC);
CREATE INDEX IF NOT EXISTS idx_weather_docs_issued_at ON weather_documents(issued_at DESC);

-- Create weather_embeddings table
CREATE TABLE IF NOT EXISTS weather_embeddings (
    id SERIAL PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES weather_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384),
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(document_id, chunk_index)
);

-- Create index on weather_embeddings for vector similarity search
CREATE INDEX IF NOT EXISTS idx_weather_embeddings_vector 
ON weather_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- Create index for foreign key lookups
CREATE INDEX IF NOT EXISTS idx_weather_embeddings_document_id 
ON weather_embeddings(document_id);

-- ============================================================================
-- SUCCESS! Database schema initialized
-- ============================================================================

SELECT 'Database initialized successfully!' AS status;
SELECT COUNT(*) AS weather_documents_count FROM weather_documents;
SELECT COUNT(*) AS weather_embeddings_count FROM weather_embeddings;
