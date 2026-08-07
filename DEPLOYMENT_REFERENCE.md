# Deployment Quick Reference


╔══════════════════════════════════════════════════════════════════════╗
║                    DEPLOYMENT QUICK REFERENCE                         ║
╚══════════════════════════════════════════════════════════════════════╝

🌐 DIRECT LINK TO APPS PAGE
════════════════════════════════════════════════════════════════════════
Click here to go directly to Apps:

https://dbc-7c939204-7e56.cloud.databricks.com/apps


📋 APP CONFIGURATION TO USE
════════════════════════════════════════════════════════════════════════
When creating the app, use these exact values:

  App Name:
  weather-retrieval-service

  Source Path:
  /Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service

  Description:
  Weather Retrieval Service with Semantic Search


🖥️  METHOD 2: CLI DEPLOYMENT (If you have terminal access)
════════════════════════════════════════════════════════════════════════
If you have the Databricks CLI installed on your local machine:

# Navigate to the project
cd /path/to/your/local/Vector-Weather-Retrieval-Service

# Create and deploy the app
databricks apps create weather-retrieval-service \
  --source-code-path /Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service \
  --description "Weather Retrieval Service with Semantic Search"

# Check status
databricks apps get weather-retrieval-service

# View logs
databricks apps logs weather-retrieval-service


🔗 YOUR APP URL (after deployment)
════════════════════════════════════════════════════════════════════════
https://dbc-7c939204-7e56.cloud.databricks.com/apps/weather-retrieval-service


⏱️  DEPLOYMENT TIMELINE
════════════════════════════════════════════════════════════════════════
  0:00 - Creating app compute
  0:30 - Installing dependencies (torch, transformers, flask, etc.)
  2:00 - Starting Flask server
  2:30 - App ready! ✅


📊 WHAT TO DO AFTER DEPLOYMENT
════════════════════════════════════════════════════════════════════════

1. Open the app URL in your browser

2. Initialize database (if not done):
   - Option A: Connect via psql and run sql/00_setup.sql
   - Option B: Run initialize_db.py from standard compute
   - Option C: The app will auto-create tables on first use

3. Sync weather data:
   - Go to "Sync Data" tab
   - Enter coordinates: 41.8781,-87.6298 (Chicago)
   - Click "Sync Weather Data"

4. Generate embeddings:
   - Run: python ingest_weather_embeddings.py
   - Or wait for the app to generate them on first search

5. Try semantic search:
   - Search: "tornado warnings near Chicago"
   - Search: "winter storm forecast"
   - Search: "heat advisory"


🔧 TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════

Issue: Can't find Apps page
→ Try: https://dbc-7c939204-7e56.cloud.databricks.com/compute/apps
→ Or look under: Compute > Apps, or Machine Learning > Apps

Issue: App creation fails
→ Check if Apps are enabled in your workspace
→ Contact your workspace admin

Issue: Deployment takes too long
→ Torch installation can take 1-2 minutes
→ Wait up to 5 minutes before investigating

Issue: App starts but shows errors
→ Check logs in the Apps UI
→ Verify database connection string is correct
→ Ensure database is accessible from Databricks


═══════════════════════════════════════════════════════════════════════
