# Lakebase Setup Guide for Weather Retrieval Service


🔐 STEP 3: Store Connection String as Secret
════════════════════════════════════════════════════════════════════════

Now that you have your Lakebase connection URL, store it securely!

Your setup_secrets.py file (currently open) will:
  ✓ Create/use the 'database' secret scope
  ✓ Store your connection URL as 'lakebase-url' secret
  ✓ Grant READ permission to workspace users


📝 CONNECTION STRING FORMAT
────────────────────────────────────────────────────────────────────────

Your connection string should look like:

  postgresql://token:<access-token>@<host>:<port>/<database>

Example:
  postgresql://token:dapi1234abcd@lakebase-abc123.cloud.databricks.com:5432/weather_db


🔑 AUTHENTICATION OPTIONS
────────────────────────────────────────────────────────────────────────

Option 1: Personal Access Token (quickest for testing)
  • Go to: User Settings > Developer > Access tokens
  • Click "Generate new token"
  • Copy the token
  • Use: postgresql://token:<your-token>@<host>:5432/<db>

Option 2: OAuth Token (recommended for production apps)
  • Apps automatically get OAuth tokens
  • No manual token management needed
  • Better security and audit trail

Option 3: Username/Password
  • Use your Databricks username and password
  • Format: postgresql://<email>:<password>@<host>:5432/<db>
  • Less secure - not recommended


▶️  READY TO RUN setup_secrets.py
════════════════════════════════════════════════════════════════════════

Before running, make sure:
  □ You have your Lakebase instance running
  □ You have the full connection string ready
  □ You've copied it to your clipboard

To run the file:
  1. Click the "Run File" button (▶️) at the top
  2. When prompted, paste your connection string
  3. Approve the ACL permission request

The secret will be stored and available to your app!


📊 STEP 4: Initialize Database Schema
════════════════════════════════════════════════════════════════════════

After storing the secret, set up your database tables:

Option A: From Your Local Machine
  psql -h <lakebase-host> -d <database> -U token \
    -f sql/00_setup.sql

Option B: From Databricks Notebook
  Run the SQL files using the lakebase.py helpers:
  
  import lakebase
  with open('sql/00_setup.sql') as f:
      setup_sql = f.read()
      lakebase.run_write(setup_sql)


✅ VERIFICATION CHECKLIST
════════════════════════════════════════════════════════════════════════

After completing setup, verify:

□ Lakebase project created and running
□ Connection string obtained
□ Secret stored (run setup_secrets.py)
□ Database schema initialized (sql/00_setup.sql)
□ Test connection:
    import lakebase
    conn = lakebase.get_connection()
    print("✓ Connected to Lakebase!")


🆘 TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════

Issue: "Lakebase not available in workspace"
→ Contact your workspace admin
→ Lakebase requires specific workspace tiers

Issue: "Secret scope already exists"
→ Uncomment line 15 in setup_secrets.py to skip creation
→ Or delete existing scope first

Issue: "Authentication failed"
→ Verify token is valid
→ Check token has DB_CONNECT permission
→ Try regenerating access token

Issue: "Cannot connect to database"
→ Ensure Lakebase instance is running (not paused)
→ Check firewall/network settings
→ Verify host/port/database name are correct


💡 QUICK START FOR EXISTING LAKEBASE
════════════════════════════════════════════════════════════════════════

If you already have a Lakebase instance:

1. Run the listing script to get your connection string:
   python list_lakebase_projects.py

2. Copy the connection string shown

3. Run setup_secrets.py:
   python setup_secrets.py
   (or click "Run File" button in the editor)

4. Paste your connection string when prompted

5. Done! The app can now connect to your database.


═══════════════════════════════════════════════════════════════════════


## Additional Resources

### Lakebase Documentation
- Official Docs: https://docs.databricks.com/en/lakehouse-federation/lakebase.html
- API Reference: https://docs.databricks.com/api/workspace/postgres

### Helper Scripts Created
- `create_lakebase.py` - Create a new Lakebase project
- `list_lakebase_projects.py` - List existing projects and get connection strings
- `setup_secrets.py` - Store connection string as secret (CURRENT FILE)

### Connection String Format
```
postgresql://token:<access-token>@<host>:<port>/<database>
```

### Example Connection String
```
postgresql://token:dapi1234567890abcdef@lakebase-12345.cloud.databricks.com:5432/main
```

### Next Steps After Setup
1. Deploy the app (see DEPLOYMENT_STEPS.md)
2. Sync weather data via UI
3. Generate embeddings: `python notebooks/ingest_weather_embeddings.py`
4. Test semantic search!

---
Generated for Weather Retrieval Service
