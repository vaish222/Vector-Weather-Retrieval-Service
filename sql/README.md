# SQL Database Schema

This directory contains SQL scripts to set up the weather retrieval database schema.

## Quick Start

Run the master setup script to create all tables, indexes, and functions:

```bash
psql -h <lakebase-host> -d <database> -f 00_setup.sql
```

Or from Python using lakebase.py:

```python
import lakebase

# Run setup
with open('sql/00_setup.sql') as f:
    setup_sql = f.read()
    lakebase.run_write(setup_sql)
```

## Files

1. **00_setup.sql** - Master setup script (run this first)
2. **01_weather_documents.sql** - Main weather data table
3. **02_weather_embeddings.sql** - Vector embeddings table with pgvector
4. **03_helper_functions.sql** - Utility functions

## Tables

### weather_documents
Stores raw weather data from NWS API:
- Alerts (severe weather warnings, watches, advisories)
- Forecasts (short-term and extended predictions)

**Key columns:**
- `id` - Stable identifier from NWS API
- `location` - Human-readable location
- `source_type` - 'alert' or 'forecast'
- `narrative_text` - Main content for semantic search
- `embedded` - Flag for embedding generation status
- `payload` - Complete raw API response (JSONB)

**Indexes:**
- Location, source type, expiration date
- Embedded flag (for finding docs needing embeddings)
- GIN index on JSONB payload

### weather_embeddings
Stores vector embeddings for semantic search:
- Text chunks (800 chars with 100 char overlap)
- 384-dimensional vectors (sentence-transformers/all-MiniLM-L6-v2)
- HNSW index for fast approximate nearest neighbor search

**Key columns:**
- `document_id` - Foreign key to weather_documents
- `chunk_index` - Position in document
- `chunk_text` - The text chunk
- `embedding` - vector(384) for similarity search

**Indexes:**
- HNSW index for cosine similarity search
- Document ID for joining

## Views

### active_weather_alerts
Shows currently active weather alerts ordered by severity.

### recent_forecasts
Shows weather forecasts from the last 7 days.

### embedding_coverage
Shows embedding generation progress by location.

## Helper Functions

### cleanup_expired_documents(days_to_keep)
Removes expired documents older than N days (default 30).

```sql
SELECT cleanup_expired_documents(30);
```

### get_document_stats()
Returns comprehensive statistics about the collection.

```sql
SELECT * FROM get_document_stats();
```

### mark_document_embedded(doc_id)
Marks a document as having embeddings generated.

```sql
SELECT mark_document_embedded('alert-abc123');
```

### search_similar_weather(query_embedding, result_limit, source_filter)
Performs semantic search using cosine similarity.

```sql
SELECT * FROM search_similar_weather(
    '[0.1, 0.2, ...]'::vector(384),
    10,
    'alert'
);
```

## Example Queries

### Find active severe weather alerts
```sql
SELECT location, event, headline, severity
FROM active_weather_alerts
WHERE severity IN ('Extreme', 'Severe')
ORDER BY issued_at DESC;
```

### Get recent forecasts for a location
```sql
SELECT headline, narrative_text, temperature, wind_speed
FROM recent_forecasts
WHERE location LIKE '%Chicago%'
LIMIT 5;
```

### Semantic search for similar weather
```sql
-- First, get the query embedding (from your application)
-- Then search for similar weather descriptions
SELECT 
    d.headline,
    d.location,
    e.chunk_text,
    1 - (e.embedding <=> $1::vector(384)) as similarity
FROM weather_embeddings e
JOIN weather_documents d ON e.document_id = d.id
ORDER BY e.embedding <=> $1::vector(384)
LIMIT 10;
```

### Check embedding generation progress
```sql
SELECT * FROM embedding_coverage;
```

## pgvector Distance Operators

The `weather_embeddings` table uses pgvector for similarity search:

- `<=>` - Cosine distance (used in this project)
- `<->` - Euclidean (L2) distance
- `<#>` - Negative inner product

**Example:**
```sql
-- Find 5 most similar weather chunks
SELECT chunk_text, embedding <=> $1::vector(384) as distance
FROM weather_embeddings
ORDER BY embedding <=> $1::vector(384)
LIMIT 5;
```

## Schema Maintenance

### Vacuum and analyze (for performance)
```sql
VACUUM ANALYZE weather_documents;
VACUUM ANALYZE weather_embeddings;
```

### Reindex (if needed)
```sql
REINDEX TABLE weather_embeddings;
```

### Check table sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('weather_documents', 'weather_embeddings')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Requirements

- PostgreSQL 13+
- pgvector extension (for vector similarity search)
- Lakebase (Databricks-managed Postgres with pgvector support)

## Notes

- The HNSW index is optimized for cosine similarity search
- Chunk size: 800 characters with 100 character overlap
- Embedding model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- Foreign key cascades: Deleting a document deletes its embeddings
