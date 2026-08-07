-- helper_functions.sql
-- Utility functions for the weather retrieval system

-- Function to clean up expired weather documents
CREATE OR REPLACE FUNCTION cleanup_expired_documents(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete documents that expired more than N days ago
    WITH deleted AS (
        DELETE FROM weather_documents
        WHERE expires_at IS NOT NULL 
          AND expires_at < CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL
        RETURNING id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_documents IS 
    'Removes weather documents that expired more than N days ago (default 30)';


-- Function to get document statistics
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
) AS $$
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
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_document_stats IS 
    'Returns comprehensive statistics about the weather document collection';


-- Function to mark documents as embedded
CREATE OR REPLACE FUNCTION mark_document_embedded(doc_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE weather_documents 
    SET embedded = TRUE 
    WHERE id = doc_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION mark_document_embedded IS 
    'Marks a document as having embeddings generated';


-- Function to search similar weather descriptions
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
) AS $$
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
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION search_similar_weather IS 
    'Performs semantic search on weather embeddings using cosine similarity';


-- Example usage:
-- 
-- -- Get statistics
-- SELECT * FROM get_document_stats();
-- 
-- -- Clean up old documents
-- SELECT cleanup_expired_documents(30);
-- 
-- -- Mark document as embedded
-- SELECT mark_document_embedded('alert-abc123');
