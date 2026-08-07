-- weather_documents.sql
-- Table to store raw weather data from NWS API (National Weather Service)
-- Supports both alerts and forecasts with flexible JSONB payload

CREATE TABLE IF NOT EXISTS weather_documents (
    -- Primary key: stable identifier from NWS or generated
    id TEXT PRIMARY KEY,
    
    -- Location information
    location TEXT NOT NULL,  -- Human-readable location (e.g., "Chicago, IL")
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    
    -- Document type and classification
    source_type TEXT NOT NULL,  -- 'alert' or 'forecast'
    headline TEXT,              -- Main headline/title
    event TEXT,                 -- Alert event type (e.g., "Severe Thunderstorm Warning")
    severity TEXT,              -- Alert severity: "Extreme", "Severe", "Moderate", "Minor", "Unknown"
    urgency TEXT,               -- Alert urgency: "Immediate", "Expected", "Future", "Past", "Unknown"
    certainty TEXT,             -- Alert certainty: "Observed", "Likely", "Possible", "Unlikely", "Unknown"
    
    -- Main content for semantic search
    narrative_text TEXT NOT NULL,  -- Full description/narrative for embedding
    
    -- Temporal information
    issued_at TIMESTAMP,        -- When the document was issued
    effective_at TIMESTAMP,     -- When it becomes effective
    expires_at TIMESTAMP,       -- When it expires
    onset_at TIMESTAMP,         -- Alert onset time (if applicable)
    ends_at TIMESTAMP,          -- Alert end time (if applicable)
    
    -- Weather data fields
    temperature INTEGER,        -- Temperature in Fahrenheit
    wind_speed TEXT,            -- Wind speed (e.g., "10 mph")
    wind_direction TEXT,        -- Wind direction (e.g., "SW")
    short_forecast TEXT,        -- Brief forecast summary
    detailed_forecast TEXT,     -- Detailed forecast text
    
    -- Raw payload for reference
    payload JSONB,              -- Complete raw API response
    
    -- Tracking fields
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When synced to database
    embedded BOOLEAN DEFAULT FALSE,                  -- Whether embeddings have been generated
    
    -- Indexes for common queries
    CONSTRAINT valid_source_type CHECK (source_type IN ('alert', 'forecast'))
);

-- Index on location for filtering by geographic area
CREATE INDEX IF NOT EXISTS idx_weather_documents_location 
    ON weather_documents(location);

-- Index on source_type for filtering alerts vs forecasts
CREATE INDEX IF NOT EXISTS idx_weather_documents_source_type 
    ON weather_documents(source_type);

-- Index on expires_at for cleaning up old documents
CREATE INDEX IF NOT EXISTS idx_weather_documents_expires_at 
    ON weather_documents(expires_at);

-- Index on embedded flag to find documents needing embeddings
CREATE INDEX IF NOT EXISTS idx_weather_documents_embedded 
    ON weather_documents(embedded) 
    WHERE embedded = FALSE;

-- Index on synced_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_weather_documents_synced_at 
    ON weather_documents(synced_at DESC);

-- Composite index for active alerts
CREATE INDEX IF NOT EXISTS idx_weather_documents_active_alerts 
    ON weather_documents(source_type, expires_at) 
    WHERE source_type = 'alert' AND expires_at > CURRENT_TIMESTAMP;

-- JSONB index for payload searches (GIN index)
CREATE INDEX IF NOT EXISTS idx_weather_documents_payload 
    ON weather_documents USING GIN(payload);

-- Comments for documentation
COMMENT ON TABLE weather_documents IS 
    'Stores weather data from NWS API including alerts and forecasts';

COMMENT ON COLUMN weather_documents.id IS 
    'Stable identifier from NWS API or generated hash';

COMMENT ON COLUMN weather_documents.narrative_text IS 
    'Main text content used for generating embeddings and semantic search';

COMMENT ON COLUMN weather_documents.embedded IS 
    'Flag indicating whether text embeddings have been generated for this document';

COMMENT ON COLUMN weather_documents.payload IS 
    'Complete raw JSON response from NWS API for reference and debugging';
