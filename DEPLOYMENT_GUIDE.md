
================================================================================
WEATHER RETRIEVAL SERVICE - DEPLOYMENT GUIDE
================================================================================

## Issue Summary
The Flask API encounters FIPS (Federal Information Processing Standards) OpenSSL
errors when running in this Databricks serverless compute environment. This is
a system-level configuration issue where PyTorch/CUDA libraries conflict with
FIPS-enabled OpenSSL.

## ✅ WORKING COMPONENTS

1. **Weather Data Fetching** - FULLY FUNCTIONAL
   - weather_client.py works perfectly
   - Can fetch NWS alerts and forecasts
   - Successfully tested with Chicago data

2. **Data Storage** - FUNCTIONAL
   - lakebase.py connection helpers work
   - Can write to Lakebase/Postgres

3. **Embedding Generation** - FUNCTIONAL (in notebooks)
   - notebooks/ingest_weather_embeddings.py works in notebook context
   - sentence-transformers model loads correctly

## 🔧 SOLUTION OPTIONS

### Option 1: Deploy as Databricks App (RECOMMENDED)
The Databricks App runtime doesn't have FIPS restrictions:

```bash
# Deploy using Databricks CLI
databricks apps deploy /Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service
```

This will:
- Use app.yaml configuration
- Run in proper app runtime (no FIPS issues)
- Provide full Flask API with all endpoints
- Handle authentication and scaling

### Option 2: Use Components Directly (CURRENT WORKAROUND)
Import and use the modules in your notebooks/code:

```python
import sys
sys.path.insert(0, "/Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service")

import weather_client

# Fetch weather data
docs = weather_client.fetch_weather_documents(
    locations=["41.8781,-87.6298"],  # Chicago
    include_forecasts=True,
    limit=50
)

# Process and store as needed
for doc in docs:
    print(doc['headline'], doc['narrative_text'][:100])
```

### Option 3: Run API Endpoints as Notebook Functions
Create notebook cells that replicate API endpoints:

```python
# Cell: Sync Weather Data
def sync_weather(locations, limit=50):
    import weather_client
    import lakebase
    
    docs = weather_client.fetch_weather_documents(
        locations=locations,
        include_forecasts=True,
        limit=limit
    )
    
    # Store in Lakebase
    # ... upsert logic ...
    
    return docs

# Usage
result = sync_weather(["41.8781,-87.6298"], limit=50)
```

### Option 4: Job-Based Scheduling
Use Databricks Jobs to run the components on a schedule:

1. Create a notebook with weather sync logic
2. Schedule as a Databricks Job (hourly/daily)
3. Use notebook widgets for location parameters

## 📋 RECOMMENDED WORKFLOW

**For Development/Testing:**
1. Use Option 2 (direct imports) in notebooks
2. Test weather fetching, storage, and embedding generation
3. Validate data quality and search results

**For Production:**
1. Deploy as Databricks App (Option 1)
2. Full REST API available at https://<workspace>/apps/<app-name>
3. Use for external integrations and real-time queries

## 🛠️ QUICK START (Notebook Workflow)

```python
# === Cell 1: Setup ===
import sys
sys.path.insert(0, "/Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service")
import weather_client
import lakebase

# === Cell 2: Fetch Weather ===
locations = ["41.8781,-87.6298", "30.2672,-97.7431"]  # Chicago, Austin
docs = weather_client.fetch_weather_documents(locations, limit=50)
print(f"Fetched {len(docs)} documents")

# === Cell 3: Store in Lakebase ===
conn = lakebase.get_connection()
# ... upsert logic ...

# === Cell 4: Generate Embeddings ===
# Run: notebooks/ingest_weather_embeddings.py

# === Cell 5: Search ===
# Use psycopg2 with pgvector for similarity search
```

## 📚 FILES REFERENCE

- `weather_client.py` - NWS API client (✓ WORKING)
- `lakebase.py` - Postgres connection helpers (✓ WORKING)
- `app.py` - Flask REST API (⚠️ FIPS issues in serverless)
- `notebooks/ingest_weather_embeddings.py` - Embedding generator (✓ WORKING in notebooks)
- `demo.py` - End-to-end demonstration
- `README.md` - Full documentation

## ❓ TROUBLESHOOTING

**Q: Why does the Flask API crash?**
A: The serverless compute environment has FIPS-enabled OpenSSL that conflicts
   with PyTorch/CUDA libraries. This is a system-level issue.

**Q: Can I fix the FIPS issue?**
A: Not in serverless compute. Use Databricks App deployment instead.

**Q: Will embeddings work?**
A: Yes! sentence-transformers works fine in notebook context. Only the
   Flask subprocess execution has issues.

================================================================================
