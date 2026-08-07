"""
Databricks App: Weather Retrieval Service
- Serves a Flask REST API for weather data
- Fetches from NWS API via weather_client.py
- Stores in Lakebase (Databricks-managed Postgres with pgvector)
- Provides semantic search over weather embeddings

Run locally:
    python app.py
Deploy as a Databricks App using app.yaml.
"""

import json
import logging
import os
import re

import requests
from databricks.sdk import WorkspaceClient
from flask import Flask, jsonify, render_template, request

import lakebase
import weather_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-app")

app = Flask(__name__)
_w = WorkspaceClient()

# Lazy-load embedding model only when needed (to avoid FIPS issues at startup)
_embedding_model = None

def _get_embedding_model():
    """Lazy-load the embedding model on first use."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("✓ Embedding model loaded")
    return _embedding_model

def ensure_weather_tables():
    """Create weather tables in Lakebase if they don\'t exist yet."""
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

def _current_user_email() -> str:
    """
    Resolve the current user\'s email so the watchlist can be personalized.

    Databricks Apps inject the logged-in user\'s identity via the
    X-Forwarded-Email header on every request. Fall back to the Databricks
    SDK\'s current_user API for local development where that header isn\'t set.
    """
    header_email = request.headers.get("X-Forwarded-Email")
    if header_email:
        return header_email
    return _w.current_user.me().user_name


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

@app.route('/admin/initialize-db', methods=['POST'])
def initialize_database():
    """Initialize the database schema - creates all tables, indexes, and functions."""
    try:
        import subprocess
        import sys
        from pathlib import Path
        
        # Get the project directory
        project_dir = Path(__file__).parent
        
        # Run the initialization script
        result = subprocess.run(
            [sys.executable, str(project_dir / 'initialize_db.py')],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_dir)
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Database initialized successfully!',
                'output': result.stdout
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Database initialization failed',
                'error': result.stderr,
                'output': result.stdout
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(Exception)
def handle_exception(err):
    """Ensure all unhandled errors return JSON (not an HTML error page),
    so the frontend\'s resp.json() call never chokes on HTML."""
    logger.exception("Unhandled exception while processing request")
    status_code = getattr(err, "code", 500)
    if not isinstance(status_code, int):
        status_code = 500
    return jsonify({"error": str(err)}), status_code


@app.route("/")
def index():
    """Simple UI for weather retrieval service."""
    return render_template("index.html")


@app.route("/weather/sync", methods=["POST"])
def sync_weather():
    """Fetch weather data from NWS API and sync to Lakebase.
    
    POST body: {"locations": ["41.8781,-87.6298", "30.2672,-97.7431"], "limit": 50}
    """
    try:
        data = request.get_json() or {}
        locations = data.get("locations", [])
        limit = data.get("limit", 50)
        
        if not locations:
            return jsonify({"error": "locations array required"}), 400
        
        # Ensure tables exist
        ensure_weather_tables()
        
        # Fetch weather documents
        documents = weather_client.fetch_weather_documents(locations, limit=limit)
        
        if not documents:
            return jsonify({"synced": 0, "message": "No weather data found"})
        
        # Upsert into weather_documents
        synced_count = 0
        with lakebase.get_connection() as conn:
            with conn.cursor() as cur:
                for doc in documents:
                    cur.execute(
                        """
                        INSERT INTO weather_documents 
                            (id, location, source_type, headline, event, severity, urgency,
                             narrative_text, issued_at, effective_at, expires_at,
                             temperature, temperature_unit, wind_speed, wind_direction,
                             payload, synced_at, embedded)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                        ON CONFLICT (id) DO UPDATE
                        SET location = EXCLUDED.location,
                            source_type = EXCLUDED.source_type,
                            headline = EXCLUDED.headline,
                            narrative_text = EXCLUDED.narrative_text,
                            synced_at = EXCLUDED.synced_at,
                            embedded = FALSE
                        """,
                        (
                            doc["id"], doc.get("location"), doc.get("source_type"),
                            doc.get("headline"), doc.get("event"), doc.get("severity"),
                            doc.get("urgency"), doc["narrative_text"], doc.get("issued_at"),
                            doc.get("effective_at"), doc.get("expires_at"),
                            doc.get("temperature"), doc.get("temperature_unit"),
                            doc.get("wind_speed"), doc.get("wind_direction"),
                            json.dumps(doc.get("payload")), doc["synced_at"]
                        )
                    )
                    synced_count += 1
                conn.commit()
        
        return jsonify({
            "synced": synced_count,
            "message": f"Synced {synced_count} weather documents"
        })
    
    except Exception as e:
        logger.exception("Error syncing weather")
        return jsonify({"error": str(e)}), 500


@app.route("/weather/search", methods=["POST"])
def search_weather():
    """Semantic search over weather embeddings.
    
    POST body: {"query": "risk of flooding near rivers", "top_k": 5}
    """
    try:
        data = request.get_json() or {}
        query = data.get("query", "").strip()
        top_k = min(max(data.get("top_k", 5), 1), 20)  # clamp to [1, 20]
        
        if not query:
            return jsonify({"error": "query required"}), 400
        
        if not _embedding_model:
            return jsonify({"error": "Embedding model not loaded"}), 500
        
        # Embed the query
        query_embedding = _get_embedding_model().encode([query])[0].tolist()
        
        # Search weather_embeddings using pgvector cosine similarity
        results = lakebase.run_query(
            """
            SELECT 
                d.id,
                d.location,
                d.headline,
                d.source_type,
                d.narrative_text,
                e.chunk_text,
                1 - (e.embedding <=> %s::vector) AS similarity
            FROM weather_embeddings e
            JOIN weather_documents d ON d.id = e.document_id
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
            """,
            (json.dumps(query_embedding), json.dumps(query_embedding), top_k)
        )
        
        # Format results
        formatted_results = [
            {
                "id": r["id"],
                "location": r["location"],
                "headline": r["headline"],
                "source_type": r["source_type"],
                "chunk_text": r["chunk_text"],
                "similarity": float(r["similarity"])
            }
            for r in results
        ]
        
        return jsonify({
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        })
    
    except Exception as e:
        logger.exception("Error searching weather")
        return jsonify({"error": str(e)}), 500


@app.route("/weather/documents")
def list_weather_documents():
    """List weather documents already synced into Lakebase."""
    limit = int(request.args.get("limit", 100))
    rows = lakebase.run_query(
        "SELECT id, location, headline, source_type, narrative_text, synced_at FROM weather_documents ORDER BY synced_at DESC LIMIT %s",
        (limit,),
    )
    return jsonify({"documents": rows})


if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 8000))
    app.run(debug=True, host=host, port=port)
    print(f"Flask app running on http://{host}:{port}")
