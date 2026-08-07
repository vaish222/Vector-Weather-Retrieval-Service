# Database Options for Weather Retrieval Service


╔══════════════════════════════════════════════════════════════════════╗
║              LAKEBASE SETUP - ALTERNATIVE APPROACHES                  ║
╚══════════════════════════════════════════════════════════════════════╝

⚠️  NOTE: The Lakebase SDK API is not available in your current workspace.
    This could mean:
    • Lakebase is not yet enabled for your workspace
    • You're using a different Postgres/database service
    • You need to use the UI instead

═══════════════════════════════════════════════════════════════════════


🎯 OPTION 1: Use Databricks UI (RECOMMENDED)
════════════════════════════════════════════════════════════════════════

1. In your Databricks workspace, navigate to one of:
   • Compute > Lakebase
   • Data > Lakebase
   • SQL > Lakebase

2. Click "Create Lakebase Project" or "New Project"

3. Fill in details:
   • Name: weather-retrieval-db
   • Region: (match your workspace region)
   • Size: Small (for testing)

4. Click "Create" and wait 2-3 minutes

5. Once ready, click "Connect" to get your connection string

6. Copy the connection string (format: postgresql://token:xxx@host:port/db)

7. Come back here and run setup_secrets.py with that string


═══════════════════════════════════════════════════════════════════════


🎯 OPTION 2: Use External PostgreSQL + pgvector
════════════════════════════════════════════════════════════════════════

If Lakebase isn't available, you can use any PostgreSQL database with
pgvector extension:

CLOUD OPTIONS:
• AWS RDS PostgreSQL (with pgvector)
• Azure Database for PostgreSQL (with pgvector)  
• Google Cloud SQL PostgreSQL (with pgvector)
• Supabase (includes pgvector by default)
• Neon (serverless Postgres with pgvector)
• Railway.app (easy setup)

SETUP STEPS:
1. Create a PostgreSQL instance with your provider
2. Enable pgvector extension:
   CREATE EXTENSION IF NOT EXISTS vector;
   
3. Get your connection string:
   postgresql://user:password@host:5432/database
   
4. Run setup_secrets.py with your connection string
5. Run sql/00_setup.sql to create tables


═══════════════════════════════════════════════════════════════════════


🎯 OPTION 3: Quick Test with SQLite (No pgvector)
════════════════════════════════════════════════════════════════════════

For quick testing WITHOUT semantic search:

This won't support vector embeddings, but you can test the weather
data fetching and storage:

1. Modify lakebase.py to use SQLite instead
2. Skip the embeddings generation
3. Test weather data sync functionality
4. Upgrade to real Postgres later

(This is only for development/testing - not for production!)


═══════════════════════════════════════════════════════════════════════


📝 CURRENT STATUS & NEXT STEPS
════════════════════════════════════════════════════════════════════════

YOUR SITUATION:
✓ Weather Retrieval Service code is ready
✓ Flask app is ready
✓ SQL schema files are ready
✓ setup_secrets.py is open and ready
⚠️ Need: Database connection string

IMMEDIATE NEXT STEPS:

Step 1: Choose your database approach
  → Lakebase (via UI if available)
  → External PostgreSQL with pgvector
  → Contact admin to enable Lakebase

Step 2: Get your connection string
  → From Lakebase UI: Click "Connect"
  → From cloud provider: Check connection settings
  → Format: postgresql://user:pass@host:port/db

Step 3: Store the connection string
  → Run setup_secrets.py (this file)
  → Click "Run File" button
  → Paste your connection string when prompted

Step 4: Initialize database
  → Run sql/00_setup.sql on your database
  → Creates tables, indexes, and functions

Step 5: Deploy your app
  → Follow DEPLOYMENT_STEPS.md
  → Deploy as Databricks App


═══════════════════════════════════════════════════════════════════════


💡 RECOMMENDED PATH FORWARD
════════════════════════════════════════════════════════════════════════

Since Lakebase SDK isn't available, I recommend:

1. Check if Lakebase exists in your UI:
   • Go to Databricks workspace
   • Look for Compute > Lakebase or Data > Lakebase
   • If yes → create project via UI
   • If no → ask admin or use external Postgres

2. For quick testing (without waiting for Lakebase):
   • Sign up for free tier at Neon.tech or Supabase
   • Both include pgvector extension
   • Get connection string in 2 minutes
   • Run setup_secrets.py with that string
   • Test your app end-to-end

3. Once you have database working:
   • Deploy app → sync data → generate embeddings → test search
   • Switch to Lakebase later if needed


═══════════════════════════════════════════════════════════════════════


🆘 NEED HELP?
════════════════════════════════════════════════════════════════════════

Tell me which option you'd like to pursue:

A. "I want to use Lakebase - help me find it in the UI"
B. "I want to use external Postgres - recommend a provider"
C. "I already have a database - help me configure the connection"
D. "I want to test without a database first"


═══════════════════════════════════════════════════════════════════════
