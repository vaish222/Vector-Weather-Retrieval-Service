#!/usr/bin/env python3
"""
Initialize Weather Retrieval Database Schema

This script creates all tables, indexes, views, and functions needed for
the weather retrieval service in your Lakebase/PostgreSQL database.

Usage:
    python initialize_db.py

Requires:
    - Databricks secret 'database/lakebase-url' configured
    - PostgreSQL with pgvector extension support
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import lakebase


def execute_sql_statement(cursor, sql, description):
    """Execute a SQL statement and handle errors."""
    try:
        cursor.execute(sql)
        print(f"   ✓ {description}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print(f"   ~ {description} (already exists)")
            return True
        else:
            print(f"   ✗ {description}")
            print(f"     Error: {error_msg}")
            return False


def main():
    print("\n" + "="*70)
    print("INITIALIZING WEATHER RETRIEVAL DATABASE SCHEMA")
    print("="*70)
    
    try:
        # Connect to database
        print("\n📡 Connecting to database...")
        conn = lakebase.get_connection()
        cursor = conn.cursor()
        print("   ✓ Connected successfully")
        
        # Step 1: Enable extensions
        print("\n📦 Step 1: Enable PostgreSQL extensions")
        print("="*70)
        
        execute_sql_statement(
            cursor,
            "CREATE EXTENSION IF NOT EXISTS vector;",
            "Enable pgvector extension"
        )
        
        execute_sql_statement(
            cursor,
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            "Enable pg_trgm extension"
        )
        
        conn.commit()
        
        # Step 2: Create weather_documents table
        print("\n📊 Step 2: Create weather_documents table")
        print("="*70)
        
        weather_documents_sql = """
CREATE TABLE IF NOT EXISTS weather_documents (
    id TEXT PRIMARY KEY,
    location TEXT NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    source_type TEXT NOT NULL,
    headline TEXT,
    event TEXT,
    severity TEXT,
    urgency TEXT,
    certainty TEXT,
    narrative_text TEXT NOT NULL,
    issued_at TIMESTAMP,
    effective_at TIMESTAMP,
    expires_at TIMESTAMP,
    onset_at TIMESTAMP,
    ends_at TIMESTAMP,
    temperature INTEGER,
    wind_speed TEXT,
    wind_direction TEXT,
    short_forecast TEXT,
    detailed_forecast TEXT,
    payload JSONB,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedded BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_source_type CHECK (source_type IN ('alert', 'forecast'))
);
        """
        
        execute_sql_statement(
            cursor,
            weather_documents_sql,
            "Create weather_documents table"
        )
        
        # Create indexes for weather_documents
        print("\n   Creating indexes...")
        
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_location ON weather_documents(location);",
             "Index on location"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_source_type ON weather_documents(source_type);",
             "Index on source_type"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_expires_at ON weather_documents(expires_at);",
             "Index on expires_at"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_embedded ON weather_documents(embedded) WHERE embedded = FALSE;",
             "Index on embedded flag"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_synced_at ON weather_documents(synced_at DESC);",
             "Index on synced_at"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_active_alerts ON weather_documents(source_type, expires_at) WHERE source_type = 'alert' AND expires_at > CURRENT_TIMESTAMP;",
             "Composite index for active alerts"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_documents_payload ON weather_documents USING GIN(payload);",
             "JSONB GIN index on payload"),
        ]
        
        for sql, desc in indexes:
            execute_sql_statement(cursor, sql, desc)
        
        conn.commit()
        
        # Step 3: Create weather_embeddings table
        print("\n🔍 Step 3: Create weather_embeddings table")
        print("="*70)
        
        weather_embeddings_sql = """
CREATE TABLE IF NOT EXISTS weather_embeddings (
    id BIGSERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    model_name TEXT DEFAULT 'sentence-transformers/all-MiniLM-L6-v2',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_document 
        FOREIGN KEY (document_id) 
        REFERENCES weather_documents(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_document_chunk 
        UNIQUE (document_id, chunk_index)
);
        """
        
        execute_sql_statement(
            cursor,
            weather_embeddings_sql,
            "Create weather_embeddings table"
        )
        
        # Create indexes for weather_embeddings
        print("\n   Creating vector indexes...")
        
        embedding_indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_weather_embeddings_hnsw ON weather_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);",
             "HNSW index for fast similarity search"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_embeddings_document_id ON weather_embeddings(document_id);",
             "Index on document_id"),
            ("CREATE INDEX IF NOT EXISTS idx_weather_embeddings_created_at ON weather_embeddings(created_at DESC);",
             "Index on created_at"),
        ]
        
        for sql, desc in embedding_indexes:
            execute_sql_statement(cursor, sql, desc)
        
        conn.commit()
        
        # Step 4: Create helper functions
        print("\n⚙️  Step 4: Create helper functions")
        print("="*70)
        
        # Function 1: cleanup_expired_documents
        cleanup_function_sql = """
CREATE OR REPLACE FUNCTION cleanup_expired_documents(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM weather_documents
        WHERE expires_at IS NOT NULL 
          AND expires_at < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;
        """
        
        execute_sql_statement(
            cursor,
            cleanup_function_sql,
            "Function: cleanup_expired_documents()"
        )
        
        # Function 2: get_document_stats
        stats_function_sql = """
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents BIGINT,
    total_alerts BIGINT,
    total_forecasts BIGINT,
    embedded_documents BIGINT,
    pending_embeddings BIGINT,
    total_embeddings BIGINT,
    unique_locations BIGINT,
    oldest_document TIMESTAMP,
    newest_document TIMESTAMP
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_documents,
        COUNT(*) FILTER (WHERE source_type = 'alert')::BIGINT as total_alerts,
        COUNT(*) FILTER (WHERE source_type = 'forecast')::BIGINT as total_forecasts,
        COUNT(*) FILTER (WHERE embedded = TRUE)::BIGINT as embedded_documents,
        COUNT(*) FILTER (WHERE embedded = FALSE)::BIGINT as pending_embeddings,
        (SELECT COUNT(*)::BIGINT FROM weather_embeddings) as total_embeddings,
        COUNT(DISTINCT location)::BIGINT as unique_locations,
        MIN(synced_at) as oldest_document,
        MAX(synced_at) as newest_document
    FROM weather_documents;
END;
$ LANGUAGE plpgsql;
        """
        
        execute_sql_statement(
            cursor,
            stats_function_sql,
            "Function: get_document_stats()"
        )
        
        # Function 3: mark_document_embedded
        mark_embedded_sql = """
CREATE OR REPLACE FUNCTION mark_document_embedded(doc_id TEXT)
RETURNS BOOLEAN AS $
BEGIN
    UPDATE weather_documents 
    SET embedded = TRUE 
    WHERE id = doc_id;
    RETURN FOUND;
END;
$ LANGUAGE plpgsql;
        """
        
        execute_sql_statement(
            cursor,
            mark_embedded_sql,
            "Function: mark_document_embedded()"
        )
        
        # Function 4: search_similar_weather
        search_function_sql = """
CREATE OR REPLACE FUNCTION search_similar_weather(
    query_embedding vector(384),
    result_limit INTEGER DEFAULT 10,
    source_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    document_id TEXT,
    chunk_text TEXT,
    headline TEXT,
    location TEXT,
    source_type TEXT,
    issued_at TIMESTAMP,
    similarity_score FLOAT
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        e.document_id,
        e.chunk_text,
        d.headline,
        d.location,
        d.source_type,
        d.issued_at,
        1 - (e.embedding <=> query_embedding) as similarity_score
    FROM weather_embeddings e
    JOIN weather_documents d ON e.document_id = d.id
    WHERE source_filter IS NULL OR d.source_type = source_filter
    ORDER BY e.embedding <=> query_embedding
    LIMIT result_limit;
END;
$ LANGUAGE plpgsql;
        """
        
        execute_sql_statement(
            cursor,
            search_function_sql,
            "Function: search_similar_weather()"
        )
        
        conn.commit()
        
        # Step 5: Create views
        print("\n👁️  Step 5: Create convenience views")
        print("="*70)
        
        # View 1: active_weather_alerts
        active_alerts_view = """
CREATE OR REPLACE VIEW active_weather_alerts AS
SELECT 
    id, location, event, severity, urgency, headline, narrative_text,
    issued_at, expires_at, synced_at
FROM weather_documents
WHERE source_type = 'alert'
  AND expires_at > CURRENT_TIMESTAMP
ORDER BY severity DESC, issued_at DESC;
        """
        
        execute_sql_statement(
            cursor,
            active_alerts_view,
            "View: active_weather_alerts"
        )
        
        # View 2: recent_forecasts
        recent_forecasts_view = """
CREATE OR REPLACE VIEW recent_forecasts AS
SELECT 
    id, location, headline, narrative_text, temperature, wind_speed,
    wind_direction, issued_at, synced_at
FROM weather_documents
WHERE source_type = 'forecast'
  AND synced_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY synced_at DESC;
        """
        
        execute_sql_statement(
            cursor,
            recent_forecasts_view,
            "View: recent_forecasts"
        )
        
        # View 3: embedding_coverage
        embedding_coverage_view = """
CREATE OR REPLACE VIEW embedding_coverage AS
SELECT 
    location,
    COUNT(*) as total_documents,
    COUNT(*) FILTER (WHERE embedded = TRUE) as embedded_count,
    COUNT(*) FILTER (WHERE embedded = FALSE) as pending_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE embedded = TRUE) / COUNT(*), 2) as coverage_percent
FROM weather_documents
GROUP BY location
ORDER BY total_documents DESC;
        """
        
        execute_sql_statement(
            cursor,
            embedding_coverage_view,
            "View: embedding_coverage"
        )
        
        conn.commit()
        
        # Step 6: Verify setup
        print("\n✅ Step 6: Verify schema")
        print("="*70)
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\n📊 Tables:")
        for table in tables:
            print(f"   ✓ {table}")
        
        # Check views
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        views = [row[0] for row in cursor.fetchall()]
        
        print("\n👁️  Views:")
        for view in views:
            print(f"   ✓ {view}")
        
        # Get row counts
        print("\n📈 Current data:")
        cursor.execute("SELECT COUNT(*) FROM weather_documents;")
        doc_count = cursor.fetchone()[0]
        print(f"   • weather_documents: {doc_count} rows")
        
        cursor.execute("SELECT COUNT(*) FROM weather_embeddings;")
        emb_count = cursor.fetchone()[0]
        print(f"   • weather_embeddings: {emb_count} rows")
        
        cursor.close()
        conn.close()
        
        # Success summary
        print("\n" + "="*70)
        print("✅ DATABASE INITIALIZATION COMPLETE")
        print("="*70)
        print("\n🎉 Your Weather Retrieval database is ready!")
        print("\nNext steps:")
        print("  1. Deploy your Flask app (see DEPLOYMENT_STEPS.md)")
        print("  2. Sync weather data via the UI or API")
        print("  3. Generate embeddings: python ingest_weather_embeddings.py")
        print("  4. Start searching!")
        print("\n" + "="*70)
        
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print("\nMake sure you're running from the project root directory.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nInitialization failed. Please check the error above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
