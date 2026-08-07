# Post-Deployment Guide

App URL: https://vectore-weather-service-app-7474660735648608.aws.databricksapps.com


╔══════════════════════════════════════════════════════════════════════╗
║          🎉 WEATHER RETRIEVAL SERVICE DEPLOYED! 🎉                   ║
╚══════════════════════════════════════════════════════════════════════╝

✅ Status: ACTIVE
📦 App Name: vectore-weather-service-app
🌐 App URL: https://vectore-weather-service-app-7474660735648608.aws.databricksapps.com


🚀 YOUR APP IS LIVE!
════════════════════════════════════════════════════════════════════════

Click this URL to access your Weather Retrieval Service:

👉 https://vectore-weather-service-app-7474660735648608.aws.databricksapps.com

You should see:
  • Modern web interface
  • Semantic search box
  • Tabs for Sync Data, Documents, and Statistics


📋 IMMEDIATE NEXT STEPS
════════════════════════════════════════════════════════════════════════

Step 1: Test the App ✓
────────────────────────────────────────────────────────────────────────
Open the URL above in your browser. You should see the web UI.

Try the health check endpoint:
https://vectore-weather-service-app-7474660735648608.aws.databricksapps.com/healthz

Should return: {"status": "healthy"}


Step 2: Initialize Database Schema 📊
────────────────────────────────────────────────────────────────────────
Your database needs tables created. Choose one method:

Option A: From Your Local Machine (if you have Python + database access)
  cd /path/to/Vector-Weather-Retrieval-Service
  python initialize_db.py

Option B: Via psql (if you have PostgreSQL client)
  psql <your-connection-string> -f sql/00_setup.sql

Option C: From Standard (Non-Serverless) Notebook
  Create a notebook with standard compute
  Run: %run /Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service/initialize_db.py

Option D: Let the App Handle It
  The app will work even without tables - it will show empty results
  Tables will be created automatically when needed


Step 3: Sync Weather Data 🌤️
────────────────────────────────────────────────────────────────────────
Once database is initialized:

1. Open your app URL
2. Click "Sync Data" tab
3. Enter location coordinates, for example:
   
   Chicago: 41.8781,-87.6298
   New York: 40.7128,-74.0060
   Los Angeles: 34.0522,-118.2437
   
4. Click "Sync Weather Data"
5. You should see weather alerts and forecasts appear!


Step 4: Generate Embeddings 🔢
────────────────────────────────────────────────────────────────────────
For semantic search to work, generate vector embeddings:

From a standard (non-serverless) notebook:
  %run /Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service/ingest_weather_embeddings.py

Or from your local machine:
  python ingest_weather_embeddings.py

This will:
  • Read all weather documents from the database
  • Generate 384-dimensional embeddings using sentence-transformers
  • Store them in the weather_embeddings table


Step 5: Try Semantic Search! 🔍
────────────────────────────────────────────────────────────────────────
Once embeddings are generated:

1. Go to your app's search box
2. Try natural language queries:
   
   "tornado warnings near Chicago"
   "winter storm forecast"
   "heat advisory"
   "severe weather alerts"
   "rain forecast for tomorrow"

3. The app will find semantically similar weather data!


🎯 QUICK TEST WORKFLOW
════════════════════════════════════════════════════════════════════════

If you want to test the full system right now:

1. ✓ App is running (DONE!)
2. → Initialize database (run initialize_db.py)
3. → Open app and sync weather for Chicago
4. → Generate embeddings
5. → Try a search query!

This will take about 5-10 minutes total.


📊 VIEW YOUR APP DETAILS
════════════════════════════════════════════════════════════════════════

In the Databricks Apps UI, you can:
  • View logs (helpful for debugging)
  • Check resource usage
  • Restart the app if needed
  • Update the app (redeploy from source)


🔧 TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════

Issue: App shows "Service Unavailable"
→ Wait 1-2 minutes - Flask is still starting
→ Check logs in Apps UI for errors

Issue: Database connection errors
→ Verify your Lakebase/PostgreSQL is running
→ Check the connection string in the secret
→ Ensure network connectivity from Databricks to your database

Issue: No search results
→ Make sure you've synced weather data
→ Verify embeddings were generated
→ Check the database has data: SELECT COUNT(*) FROM weather_documents;

Issue: Search is slow on first query
→ Normal! The embedding model downloads on first use (~50MB)
→ Subsequent searches will be fast


═══════════════════════════════════════════════════════════════════════
