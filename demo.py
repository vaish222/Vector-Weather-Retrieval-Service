"""
Demo script showing the complete weather pipeline workflow.

This demonstrates:
1. Setting up tables
2. Syncing weather data from NWS API
3. Running the embedding ingestion
4. Performing semantic search

Run this after starting the Flask app.
"""

import requests
import json
import time

# API base URL (adjust if running remotely)
API_BASE = "http://localhost:8080"

def demo_sync():
    """Step 1: Sync weather data for Chicago and Austin."""
    print("\n=== Step 1: Syncing Weather Data ===")
    
    response = requests.post(
        f"{API_BASE}/weather/sync",
        json={
            "locations": [
                "41.8781,-87.6298",  # Chicago
                "30.2672,-97.7431"   # Austin, TX
            ],
            "limit": 50
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Synced {result['synced']} weather documents")
    else:
        print(f"✗ Error: {response.text}")
        return False
    
    return True


def demo_list_documents():
    """Step 2: List synced documents."""
    print("\n=== Step 2: Listing Synced Documents ===")
    
    response = requests.get(f"{API_BASE}/weather/documents?limit=5")
    
    if response.status_code == 200:
        docs = response.json()
        print(f"✓ Found {len(docs)} documents (showing first 5):")
        for doc in docs[:3]:
            print(f"  - {doc['headline']} ({doc['location']}) - {doc['source_type']}")
    else:
        print(f"✗ Error: {response.text}")


def demo_search():
    """Step 3: Perform semantic search."""
    print("\n=== Step 3: Semantic Search ===")
    
    queries = [
        "flash flood risk this weekend",
        "severe thunderstorm warnings",
        "temperature forecast for next week"
    ]
    
    for query in queries:
        print(f"\nQuery: \"{query}\"")
        
        response = requests.post(
            f"{API_BASE}/weather/search",
            json={"query": query, "top_k": 3}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Found {result['count']} results:")
            for r in result["results"]:
                print(f"  - [{r['similarity']:.3f}] {r['headline']} ({r['location']})")
                print(f"    {r['chunk_text'][:100]}...")
        else:
            print(f"✗ Error: {response.text}")


def main():
    print("="*60)
    print("Weather Retrieval Service - Demo")
    print("="*60)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/healthz", timeout=2)
        if response.status_code != 200:
            print("\n✗ API is not responding. Start the Flask app first:")
            print("  python app.py")
            return
    except:
        print("\n✗ Cannot connect to API. Start the Flask app first:")
        print("  python app.py")
        return
    
    print("\n✓ API is running")
    
    # Run demo steps
    if not demo_sync():
        return
    
    time.sleep(2)
    demo_list_documents()
    
    print("\n\nNOTE: To enable search, run the embedding ingestion:")
    print("  python notebooks/ingest_weather_embeddings.py")
    print("\nThen run this demo again to test search.")
    
    # Try search (may fail if embeddings not generated yet)
    try:
        demo_search()
    except Exception as e:
        print(f"\n(Search not available yet - run ingestion first)")


if __name__ == "__main__":
    main()
