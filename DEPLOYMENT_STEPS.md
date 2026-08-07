
╔══════════════════════════════════════════════════════════════════════╗
║            DATABRICKS APP DEPLOYMENT GUIDE                            ║
║            Weather Retrieval Service                                  ║
╚══════════════════════════════════════════════════════════════════════╝

🔐 STEP 1: Set Up Lakebase Secret
════════════════════════════════════════════════════════════════════════

Before deploying, you need to configure the database connection secret.

Option A: Run setup_secrets.py (RECOMMENDED)
────────────────────────────────────────────────────────────────────────
The file is already open in your editor. To run it:

1. Make sure you have your Lakebase connection URL ready:
   Format: postgresql://[user]:[password]@[host]:[port]/[database]

2. Click "Run File" button (or press Shift+Enter)
   
3. When prompted, paste your Lakebase URL

Note: This will:
   • Create the 'database' secret scope (if not exists)
   • Store your lakebase-url as a secret
   • Set READ permissions for workspace users


Option B: Use Databricks CLI
────────────────────────────────────────────────────────────────────────
If you prefer CLI:

# Create secret scope (if it doesn't exist)
databricks secrets create-scope database

# Add your Lakebase URL as a secret
databricks secrets put-secret database lakebase-url \
  --string-value "postgresql://[user]:[password]@[host]:[port]/[database]"


Option C: Use Databricks UI
────────────────────────────────────────────────────────────────────────
1. Go to Settings > Developer > Secrets
2. Create scope: "database"
3. Add secret key: "lakebase-url"
4. Paste your connection string


🚀 STEP 2: Deploy the App
════════════════════════════════════════════════════════════════════════

Once the secret is configured, deploy using the Databricks UI:

Method 1: Deploy via UI (EASIEST)
────────────────────────────────────────────────────────────────────────
1. Go to your workspace
2. Navigate to: /Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service
3. Right-click on the folder
4. Select "Deploy as Databricks App"
5. Follow the deployment wizard


Method 2: Deploy via CLI
────────────────────────────────────────────────────────────────────────
Open a terminal and run:

cd /Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service
databricks apps create weather-retrieval-service \
  --source-code-path . \
  --description "Weather Retrieval Service with Semantic Search"

# Check deployment status
databricks apps list


Method 3: Deploy via Databricks Asset Bundles (DABs)
────────────────────────────────────────────────────────────────────────
You have a databricks.yml file configured. To deploy:

# Validate the bundle
databricks bundle validate

# Deploy to development
databricks bundle deploy -t dev

# Check status
databricks bundle resources list


📊 STEP 3: Initialize Database Schema
════════════════════════════════════════════════════════════════════════

After deployment, set up your database tables:

# Connect to your Lakebase instance
psql -h [lakebase-host] -d [database] -U [user]

# Run the setup script
\i sql/00_setup.sql

This will create:
  • weather_documents table
  • weather_embeddings table with pgvector
  • Helper functions and views


✅ STEP 4: Verify Deployment
════════════════════════════════════════════════════════════════════════

Once deployed, your app will be available at:
https://dbc-7c939204-7e56.cloud.databricks.com/apps/weather-retrieval-service

Test the endpoints:

# Health check
curl https://[your-app-url]/healthz

# Or open in browser and use the UI
Click the app URL to access the web interface


🎯 STEP 5: Sync and Test
════════════════════════════════════════════════════════════════════════

1. Open the app UI in your browser
2. Go to "Sync Data" tab
3. Enter locations (e.g., 41.8781,-87.6298 for Chicago)
4. Click "Sync Weather Data"
5. Run the embedding script:
   python notebooks/ingest_weather_embeddings.py
6. Try a semantic search!


📋 DEPLOYMENT CHECKLIST
════════════════════════════════════════════════════════════════════════

□ Lakebase connection URL ready
□ Secret scope 'database' created
□ Secret 'lakebase-url' stored
□ App deployed (via UI, CLI, or DABs)
□ Database schema initialized (sql/00_setup.sql)
□ App URL accessible
□ Weather data synced
□ Embeddings generated
□ Search tested


🔧 TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════

Issue: "Secret not found"
→ Make sure secret scope and key are created correctly
→ Check permissions: databricks secrets list --scope database

Issue: "Database connection failed"
→ Verify Lakebase URL format
→ Check network connectivity
→ Ensure Lakebase instance is running

Issue: "App deployment failed"
→ Check app.yaml configuration
→ Verify requirements.txt dependencies
→ Review deployment logs

Issue: "Embedding model won't load"
→ First search takes 1-2 minutes (model download)
→ Check internet connectivity from app compute
→ Verify torch/transformers are installed


💡 QUICK TIPS
════════════════════════════════════════════════════════════════════════

• The app runs on Databricks App Compute (no FIPS issues!)
• Embedding model downloads on first search (~50MB)
• Use the web UI for easy interaction
• API endpoints available for programmatic access
• Logs available in App Compute UI
• Can update app by redeploying with same name


═══════════════════════════════════════════════════════════════════════
Need help? Check:
  • DEPLOYMENT_GUIDE.md in project root
  • README.md for full documentation
  • sql/README.md for database details
═══════════════════════════════════════════════════════════════════════
