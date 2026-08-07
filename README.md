# Vector-Weather-Retrieval-Service

An end-to-end semantic search system for weather data using Databricks, Lakebase (managed Postgres + pgvector), and sentence transformers.

## Overview

This service:
1. **Harvests** unstructured weather text from the National Weather Service (NWS) API
2. **Vectorizes** that text using sentence-transformers embeddings
3. **Stores** vectors in Lakebase with pgvector for fast similarity search
4. **Serves** a REST API for semantic weather search

## Architecture

```
NWS API → weather_client.py → Lakebase (weather_documents)
                                      ↓
                         ingest_weather_embeddings.py
                                      ↓
                         Lakebase (weather_embeddings + pgvector)
                                      ↓
                               Flask API (app.py)
                                      ↓
                            /weather/search endpoint
```

## Components

### 1. `weather_client.py`
Fetches weather data from api.weather.gov:
- **Active alerts**: Warnings, watches, advisories with narrative descriptions
- **Forecast narratives**: Daily and hourly forecasts with detailed text

Normalizes each into a document with:
- `id`, `location`, `source_type`, `headline`, `narrative_text`
- Timestamps: `issued_at`, `effective_at`, `expires_at`
- Raw JSON payload for provenance

### 2. `lakebase.py`
Connection helper for Databricks Lakebase (managed Postgres):
- `get_connection()`: Context manager for psycopg2 connections
- `run_query()`: Execute SELECT queries
- `run_write()`: Execute INSERT/UPDATE/DELETE

### 3. `ingest_weather_embeddings.py`
Embedding pipeline:
1. Reads unembedded rows from `weather_documents`
2. Chunks text (800 chars, 100 overlap)
3. Generates embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
4. Writes to `weather_embeddings` with pgvector HNSW index

### 4. `app.py`
Flask REST API with three endpoints:

#### `POST /weather/sync`
Fetch and store weather data:
```json
{
  "locations": ["41.8781,-87.6298", "30.2672,-97.7431"],
  "limit": 50
}
```
Returns: `{"synced": 42, "message": "..."}`

#### `POST /weather/search`
Semantic search over embeddings:
```json
{
  "query": "risk of flooding near rivers",
  "top_k": 5
}
```
Returns:
```json
{
  "query": "...",
  "results": [
    {
      "id": "...",
      "location": "...",
      "headline": "Flash Flood Warning",
      "source_type": "alert",
      "chunk_text": "...",
      "similarity": 0.87
    }
  ],
  "count": 5
}
```

#### `GET /weather/documents?limit=100`
List synced weather documents

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Lakebase Connection
Store your Lakebase connection URL in Databricks Secrets:
```bash
databricks secrets put-secret database lakebase-url
# Paste: postgresql://role:password@host:5432/databricks_postgres?sslmode=require
```

### 3. Initialize Tables
Run the ingestion script once to create tables:
```bash
python notebooks/ingest_weather_embeddings.py
```

This creates:
- `weather_documents` - raw weather text
- `weather_embeddings` - vectorized chunks with pgvector HNSW index

### 4. Run the API
```bash
python app.py
```

## Usage Example

### 1. Sync Weather Data
```bash
curl -X POST http://localhost:8080/weather/sync \
  -H "Content-Type: application/json" \
  -d '{
    "locations": ["41.8781,-87.6298", "30.2672,-97.7431"],
    "limit": 50
  }'
```

### 2. Generate Embeddings
```bash
python notebooks/ingest_weather_embeddings.py
```

### 3. Search
```bash
curl -X POST http://localhost:8080/weather/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "flash flood risk this weekend",
    "top_k": 5
  }'
```

## Location Format

Provide locations as `"lat,lon"` strings:
- Chicago: `"41.8781,-87.6298"`
- Austin, TX: `"30.2672,-97.7431"`
- Seattle: `"47.6062,-122.3321"`

The client resolves these to NWS grid coordinates automatically.

## Data Flow

1. **Harvest**: `weather_client.fetch_weather_documents()` → `weather_documents` table
2. **Vectorize**: `ingest_weather_embeddings.py` → `weather_embeddings` table
3. **Retrieve**: `/weather/search` embeds query → pgvector `<=>` operator → top-k results

## Technologies

- **Databricks**: Platform and compute
- **Lakebase**: Managed Postgres with pgvector extension
- **sentence-transformers**: all-MiniLM-L6-v2 (384-dim embeddings)
- **pgvector**: HNSW index for fast cosine similarity search
- **Flask**: REST API
- **NWS API**: Free weather data (no API key required)

## Performance Notes

- **Chunking**: 800 chars with 100-char overlap handles long alert descriptions
- **Embeddings**: 384-dim model balances quality and speed
- **Index**: HNSW (Hierarchical Navigable Small World) for sub-linear search
- **Batch size**: 50 documents per sync prevents rate-limiting

## Deployment

Deploy as a Databricks App:
```bash
databricks bundle deploy
```

See `app.yaml` for configuration.