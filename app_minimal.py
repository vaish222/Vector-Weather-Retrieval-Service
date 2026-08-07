"""
Minimal Weather API (FIPS-compatible version)
Excludes embedding search to avoid PyTorch/CUDA FIPS conflicts.
"""

import json
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
import weather_client
import lakebase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-app-minimal")

app = Flask(__name__)

@app.route("/healthz")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "version": "minimal-fips-compatible"})

@app.route("/")
def home():
    """Root endpoint with API info."""
    return jsonify({
        "service": "Weather Retrieval API (Minimal)",
        "note": "Embedding search disabled due to FIPS constraints",
        "endpoints": {
            "/healthz": "Health check",
            "/weather/sync": "POST - Sync weather data from NWS",
            "/weather/documents": "GET - List synced documents"
        }
    })

@app.route("/weather/sync", methods=["POST"])
def sync_weather():
    """Fetch weather data from NWS and store in Lakebase."""
    try:
        data = request.get_json() or {}
        locations = data.get("locations", ["41.8781,-87.6298"])  # Chicago default
        limit = data.get("limit", 50)
        
        logger.info(f"Syncing weather for {len(locations)} locations...")
        
        # Fetch documents
        documents = weather_client.fetch_weather_documents(
            locations=locations,
            include_forecasts=True,
            limit=limit
        )
        
        if not documents:
            return jsonify({"message": "No weather data found", "synced": 0}), 404
        
        # Store in Lakebase
        # Note: You'll need to implement lakebase.upsert_documents() or use direct SQL
        logger.info(f"Fetched {len(documents)} documents")
        
        return jsonify({
            "message": f"Successfully fetched {len(documents)} weather documents",
            "synced": len(documents),
            "documents": documents[:5]  # Return first 5 as sample
        })
    
    except Exception as e:
        logger.error(f"Error syncing weather: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/weather/documents")
def list_documents():
    """List stored weather documents from Lakebase."""
    try:
        limit = int(request.args.get("limit", 10))
        
        # Query Lakebase
        # Note: Implement lakebase.query() to fetch documents
        conn = lakebase.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, location, source_type, headline, synced_at
                FROM weather_documents
                ORDER BY synced_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        
        documents = []
        for row in rows:
            documents.append({
                "id": row[0],
                "location": row[1],
                "source_type": row[2],
                "headline": row[3],
                "synced_at": row[4]
            })
        
        return jsonify({
            "count": len(documents),
            "documents": documents
        })
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting minimal Weather API (FIPS-compatible)")
    logger.info("Embedding search disabled - use ingest_weather_embeddings.py separately")
    app.run(host="0.0.0.0", port=8080, debug=True)
