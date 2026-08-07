-- setup.sql
-- Master setup script - run this to initialize the entire database schema

-- Step 1: Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search optimizations

-- Step 2: Create main tables
\i 01_weather_documents.sql
\i 02_weather_embeddings.sql

-- Step 3: Create helper functions
\i 03_helper_functions.sql

-- Step 4: Create initial views for convenience

-- View: Active weather alerts
CREATE OR REPLACE VIEW active_weather_alerts AS
SELECT 
    id,
    location,
    event,
    severity,
    urgency,
    headline,
    narrative_text,
    issued_at,
    expires_at,
    synced_at
FROM weather_documents
WHERE source_type = 'alert'
  AND expires_at > CURRENT_TIMESTAMP
ORDER BY severity DESC, issued_at DESC;

COMMENT ON VIEW active_weather_alerts IS 
    'Shows currently active weather alerts';


-- View: Recent forecasts
CREATE OR REPLACE VIEW recent_forecasts AS
SELECT 
    id,
    location,
    headline,
    narrative_text,
    temperature,
    wind_speed,
    wind_direction,
    issued_at,
    synced_at
FROM weather_documents
WHERE source_type = 'forecast'
  AND synced_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY synced_at DESC;

COMMENT ON VIEW recent_forecasts IS 
    'Shows weather forecasts from the last 7 days';


-- View: Embedding coverage
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

COMMENT ON VIEW embedding_coverage IS 
    'Shows embedding generation progress by location';

-- Step 5: Display setup summary
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Weather Retrieval Database Setup Complete';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  ✓ weather_documents';
    RAISE NOTICE '  ✓ weather_embeddings';
    RAISE NOTICE '';
    RAISE NOTICE 'Views created:';
    RAISE NOTICE '  ✓ active_weather_alerts';
    RAISE NOTICE '  ✓ recent_forecasts';
    RAISE NOTICE '  ✓ embedding_coverage';
    RAISE NOTICE '';
    RAISE NOTICE 'Helper functions:';
    RAISE NOTICE '  ✓ cleanup_expired_documents()';
    RAISE NOTICE '  ✓ get_document_stats()';
    RAISE NOTICE '  ✓ mark_document_embedded()';
    RAISE NOTICE '  ✓ search_similar_weather()';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Sync weather data: POST /weather/sync';
    RAISE NOTICE '  2. Generate embeddings: python ingest_weather_embeddings.py';
    RAISE NOTICE '  3. Test search: POST /weather/search';
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
END $$;
