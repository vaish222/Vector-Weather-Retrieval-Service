"""NWS Weather API Client.

Fetches unstructured weather text from api.weather.gov:
- Active alerts (warnings, watches, advisories)
- Forecast narratives (daily and hourly)

Normalizes each into a document record for embedding and retrieval.
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

# NWS API base
NWS_API_BASE = "https://api.weather.gov"

# User-Agent is REQUIRED by NWS API - they block requests without it
HEADERS = {
    "User-Agent": "(Databricks Weather Service, contact@example.com)",
    "Accept": "application/geo+json"
}


def _fetch_json(url: str, retries: int = 3) -> dict | None:
    """Fetch JSON from NWS API with retries and rate-limit handling."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:  # rate limited
                logger.warning(f"Rate limited, waiting 2s before retry {attempt+1}")
                time.sleep(2)
            else:
                logger.warning(f"HTTP {resp.status_code} from {url}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(1)
    return None


def resolve_location(location: str) -> dict | None:
    """
    Resolve a location string to NWS grid coordinates.
    
    Args:
        location: Either "lat,lon" or a city/state string like "Chicago, IL"
    
    Returns:
        dict with: {"lat": float, "lon": float, "office": str, "gridX": int, "gridY": int}
        or None if resolution failed.
    """
    # Check if already lat/lon
    if "," in location:
        parts = location.strip().split(",")
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0].strip()), float(parts[1].strip())
                # Fetch grid point
                url = f"{NWS_API_BASE}/points/{lat:.4f},{lon:.4f}"
                data = _fetch_json(url)
                if data and "properties" in data:
                    props = data["properties"]
                    return {
                        "lat": lat,
                        "lon": lon,
                        "office": props.get("gridId"),
                        "gridX": props.get("gridX"),
                        "gridY": props.get("gridY"),
                        "city": props.get("relativeLocation", {}).get("properties", {}).get("city"),
                        "state": props.get("relativeLocation", {}).get("properties", {}).get("state"),
                    }
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse lat/lon from {location}: {e}")
                return None
    
    # For city/state, we\'d need a geocoding service - for now, log and skip
    logger.warning(f"City/state resolution not implemented - provide lat,lon format. Got: {location}")
    return None


def fetch_alerts(state_code: str = None, limit: int = 50) -> list[dict]:
    """
    Fetch active weather alerts.
    
    Args:
        state_code: Two-letter state code (e.g., "IL", "TX") or None for national
        limit: Max number of alerts to return
    
    Returns:
        List of normalized document dicts
    """
    url = f"{NWS_API_BASE}/alerts/active"
    if state_code:
        url += f"?area={state_code.upper()}"
    
    data = _fetch_json(url)
    if not data or "features" not in data:
        return []
    
    documents = []
    for feature in data.get("features", [])[:limit]:
        props = feature.get("properties", {})
        alert_id = props.get("id")
        if not alert_id:
            continue
        
        # Build narrative text from description + instruction
        narrative_parts = []
        if desc := props.get("description"):
            narrative_parts.append(desc)
        if instr := props.get("instruction"):
            narrative_parts.append(instr)
        narrative_text = "\n\n".join(narrative_parts)
        
        if not narrative_text:
            continue
        
        documents.append({
            "id": alert_id,
            "location": props.get("areaDesc", "Unknown"),
            "source_type": "alert",
            "headline": props.get("headline") or props.get("event") or "Weather Alert",
            "event": props.get("event"),
            "severity": props.get("severity"),
            "urgency": props.get("urgency"),
            "narrative_text": narrative_text,
            "issued_at": props.get("sent"),
            "effective_at": props.get("effective"),
            "expires_at": props.get("expires"),
            "payload": feature,
        })
    
    logger.info(f"Fetched {len(documents)} alerts")
    return documents


def fetch_forecast(grid_office: str, grid_x: int, grid_y: int, hourly: bool = False) -> list[dict]:
    """
    Fetch forecast narratives for a grid location.
    
    Args:
        grid_office: NWS office code (e.g., "LOT" for Chicago)
        grid_x, grid_y: Grid coordinates
        hourly: If True, fetch hourly forecast; else daily
    
    Returns:
        List of normalized forecast document dicts
    """
    path = "forecast/hourly" if hourly else "forecast"
    url = f"{NWS_API_BASE}/gridpoints/{grid_office}/{grid_x},{grid_y}/{path}"
    
    data = _fetch_json(url)
    if not data or "properties" not in data:
        return []
    
    periods = data["properties"].get("periods", [])
    documents = []
    
    for period in periods:
        # Create a stable ID from location + period time
        period_start = period.get("startTime", "")
        period_name = period.get("name", "")
        id_string = f"{grid_office}_{grid_x}_{grid_y}_{period_start}"
        doc_id = hashlib.md5(id_string.encode()).hexdigest()
        
        narrative = period.get("detailedForecast")
        if not narrative:
            continue
        
        documents.append({
            "id": doc_id,
            "location": f"{grid_office} grid {grid_x},{grid_y}",
            "source_type": "forecast_hourly" if hourly else "forecast_daily",
            "headline": period_name,
            "narrative_text": narrative,
            "issued_at": data["properties"].get("updateTime"),
            "effective_at": period_start,
            "expires_at": period.get("endTime"),
            "temperature": period.get("temperature"),
            "temperature_unit": period.get("temperatureUnit"),
            "wind_speed": period.get("windSpeed"),
            "wind_direction": period.get("windDirection"),
            "payload": period,
        })
    
    logger.info(f"Fetched {len(documents)} {path} periods for {grid_office} {grid_x},{grid_y}")
    return documents


def fetch_weather_documents(locations: list[str], include_forecasts: bool = True, limit: int = 100) -> list[dict]:
    """
    Fetch weather documents (alerts + forecasts) for a list of locations.
    
    Args:
        locations: List of "lat,lon" strings (e.g., ["41.8781,-87.6298"])
        include_forecasts: Whether to fetch forecast narratives
        limit: Max documents to return
    
    Returns:
        List of normalized document dicts ready for Lakebase insertion
    """
    all_docs = []
    
    # Fetch alerts (state-wide is more efficient than per-location)
    # We\'ll collect unique states from locations
    states = set()
    for loc in locations:
        resolved = resolve_location(loc)
        if resolved and resolved.get("state"):
            states.add(resolved["state"])
    
    # Fetch alerts for each state
    for state in states:
        all_docs.extend(fetch_alerts(state_code=state, limit=limit // len(states) if states else limit))
    
    # Fetch forecasts for each location
    if include_forecasts:
        for loc in locations:
            resolved = resolve_location(loc)
            if not resolved:
                continue
            
            office = resolved.get("office")
            grid_x = resolved.get("gridX")
            grid_y = resolved.get("gridY")
            
            if office and grid_x is not None and grid_y is not None:
                # Fetch daily forecast
                all_docs.extend(fetch_forecast(office, grid_x, grid_y, hourly=False))
                # Optionally fetch hourly (can be verbose)
                # all_docs.extend(fetch_forecast(office, grid_x, grid_y, hourly=True))
    
    # Add synced_at timestamp
    now = datetime.utcnow().isoformat()
    for doc in all_docs:
        doc["synced_at"] = now
    
    return all_docs[:limit]
