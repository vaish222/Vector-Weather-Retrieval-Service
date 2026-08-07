#!/usr/bin/env python3
"""
Initialize database schema from SQL files
"""
import sys
sys.path.append('/Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service')

import lakebase
import os

print("\n" + "="*70)
print("INITIALIZING DATABASE SCHEMA")
print("="*70)

sql_files = [
    'sql/00_setup.sql',
    'sql/01_weather_documents.sql',
    'sql/02_weather_embeddings.sql',
    'sql/03_helper_functions.sql'
]

try:
    conn = lakebase.get_connection()
    cursor = conn.cursor()
    
    # Read and execute the master setup file
    master_sql_path = '/Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service/sql/00_setup.sql'
    
    print(f"\n📄 Reading: sql/00_setup.sql")
    with open(master_sql_path, 'r') as f:
        setup_sql = f.read()
    
    print(f"\n⚙️  Executing SQL...")
    
    # Split on semicolons and execute each statement
    statements = [s.strip() for s in setup_sql.split(';') if s.strip()]
    
    for i, statement in enumerate(statements, 1):
        if statement.strip():
            print(f"   Statement {i}/{len(statements)}...", end=' ')
            try:
                cursor.execute(statement)
                print("✓")
            except Exception as e:
                # Some statements may fail if objects already exist - that's OK
                if "already exists" in str(e).lower():
                    print("(already exists)")
                else:
                    print(f"⚠️  {e}")
    
    conn.commit()
    
    # Verify tables were created
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n✅ Schema initialized successfully!")
    print(f"\n📊 Tables created:")
    for table in tables:
        print(f"   • {table}")
    
    # Get row counts
    print(f"\n📈 Current data:")
    if 'weather_documents' in tables:
        cursor.execute("SELECT COUNT(*) FROM weather_documents;")
        doc_count = cursor.fetchone()[0]
        print(f"   • weather_documents: {doc_count} rows")
    
    if 'weather_embeddings' in tables:
        cursor.execute("SELECT COUNT(*) FROM weather_embeddings;")
        emb_count = cursor.fetchone()[0]
        print(f"   • weather_embeddings: {emb_count} rows")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Deploy your Flask app (see DEPLOYMENT_STEPS.md)")
    print("2. Sync weather data via the UI")
    print("3. Generate embeddings: python ingest_weather_embeddings.py")
    print("4. Start searching!")
    print("\n" + "="*70)
    
except FileNotFoundError as e:
    print(f"\n❌ SQL file not found: {e}")
    print("\nMake sure you're running from the project root.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
