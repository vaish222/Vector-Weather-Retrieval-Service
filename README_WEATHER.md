# Weather Vector Retrieval Service

## Data Source

This project uses the **National Weather Service (NWS) API (`api.weather.gov`)** as the weather data source.

I chose NWS because it provides free access without requiring an API key and includes useful unstructured text such as:

- Active weather alerts, warnings, watches, and advisories
- Daily forecast narratives
- Weather details such as temperature, wind speed, and wind direction

The narrative-heavy weather data is a good fit for demonstrating semantic search because users can search by meaning rather than exact keywords.

---

## Schema and Vector Design

The application stores data in **Databricks Lakebase**, a managed PostgreSQL database, and uses the **pgvector** extension for vector similarity search.

### `weather_documents`

Stores the normalized weather records retrieved from NWS.

Key columns include:

- `id` – unique document identifier
- `location` – location or NWS grid
- `source_type` – alert, daily forecast, etc.
- `headline`
- `event`
- `severity`
- `urgency`
- `narrative_text` – primary text used for embedding
- `issued_at`, `effective_at`, `expires_at`
- `temperature`, `temperature_unit`
- `wind_speed`, `wind_direction`
- `payload` – original NWS JSON for provenance
- `synced_at`
- `embedded` – tracks whether the document has been vectorized

### `weather_embeddings`

Stores the chunked text and vector representation.

Key columns include:

- `document_id` – references `weather_documents`
- `chunk_index`
- `chunk_text`
- `embedding`
- `model_name`
- `created_at`

### Chunking

Long weather narratives are divided into overlapping chunks:

- **Chunk size:** 800 characters
- **Overlap:** 100 characters

The overlap helps preserve context when information spans chunk boundaries.

### Embedding Model

The project uses:

`sentence-transformers/all-MiniLM-L6-v2`

- **Embedding dimensions:** 384
- **Vector storage:** `pgvector`
- **Similarity metric:** cosine similarity
- **Index:** HNSW

This model provides a practical balance between semantic-search quality, vector size, and execution speed for a lightweight retrieval service.

---

## Running the Pipeline End-to-End

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Lakebase

Store the Lakebase PostgreSQL connection URL in Databricks Secrets:

```bash
databricks secrets put-secret database lakebase-url
```

### 3. Start the Flask application

```bash
python app.py
```

### 4. Sync weather data

Call the `/weather/sync` endpoint with latitude/longitude locations:

```bash
curl -X POST http://localhost:8080/weather/sync \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      "41.8781,-87.6298",
      "30.2672,-97.7431"
    ],
    "limit": 50
  }'
```

This retrieves NWS alerts and forecasts, normalizes them, and stores them in `weather_documents`.

### 5. Generate embeddings

Run:

```bash
python notebooks/ingest_weather_embeddings.py
```

The script:

1. Reads documents where `embedded = false`
2. Splits each narrative into 800-character chunks with 100-character overlap
3. Generates 384-dimensional embeddings
4. Stores the chunks and vectors in `weather_embeddings`
5. Marks the original document as embedded

### 6. Run semantic search

```bash
curl -X POST http://localhost:8080/weather/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "flash flood risk this weekend",
    "top_k": 5
  }'
```

The service embeds the search query using the same model and compares it with stored vectors using pgvector cosine similarity. The highest-ranking chunks are returned with weather-document metadata and similarity scores.

### Pipeline Summary

```text
NWS API
   ↓
/weather/sync
   ↓
weather_documents
   ↓
ingest_weather_embeddings.py
   ↓
Chunk + Embed
   ↓
weather_embeddings (pgvector)
   ↓
/weather/search
   ↓
Top-K semantic search results
```

---

## Known Limitations and Future Improvements

Given more time, I would improve the project in the following areas:

- **Automatic embedding pipeline:** Synchronization and embedding are separate steps today. Trigger embedding automatically after new weather data is synced.
- **Scheduled refresh:** Add a Databricks Job or scheduled workflow to periodically refresh weather data.
- **Location support:** The current implementation primarily uses latitude/longitude. Add geocoding so users can enter city/state names.
- **Hourly forecasts:** The weather client supports hourly forecasts, but hourly ingestion is currently disabled to limit data volume.
- **Better chunking:** Replace character-based chunking with token- or sentence-aware chunking to preserve semantic boundaries.
- **Search filtering:** Add filters for location, alert type, severity, and effective date in addition to vector similarity.
- **Embedding evaluation:** Compare additional embedding models and measure retrieval quality.
- **Automated testing and monitoring:** Add unit/integration tests, health monitoring, structured logging, and retrieval-quality metrics.
- **Production scalability:** Tune indexing, batching, caching, and retention policies as the dataset grows.

---

## Technology Stack

- Databricks Apps
- Databricks Lakebase / PostgreSQL
- pgvector
- Python / Flask
- National Weather Service API
- Sentence Transformers
- `all-MiniLM-L6-v2`
