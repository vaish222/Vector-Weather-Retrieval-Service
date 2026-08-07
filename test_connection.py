#!/usr/bin/env python3
"""
Test database connection and initialize schema
"""
import sys
sys.path.append('/Workspace/Users/vaishali221@gmail.com/Vector-Weather-Retrieval-Service')

import lakebase

print("\n" + "="*70)
print("TESTING DATABASE CONNECTION")
print("="*70)

try:
    # Test connection
    conn = lakebase.get_connection()
    print("\n✅ Successfully connected to database!")
    
    # Get version
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n📊 PostgreSQL Version:")
    print(f"   {version[:80]}...")
    
    # Check if pgvector is available
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pg_extension 
        WHERE extname = 'vector';
    """)
    has_pgvector = cursor.fetchone()[0] > 0
    
    if has_pgvector:
        print("\n✅ pgvector extension is installed")
    else:
        print("\n⚠️  pgvector extension NOT found")
        print("   Run: CREATE EXTENSION vector;")
    
    # Check existing tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('weather_documents', 'weather_embeddings');
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n📋 Existing tables:")
    if existing_tables:
        for table in existing_tables:
            print(f"   ✓ {table}")
    else:
        print("   (none found - need to run sql/00_setup.sql)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("NEXT: Initialize Schema")
    print("="*70)
    if not existing_tables:
        print("\nYour database is connected but empty.")
        print("\nTo initialize the schema, run:")
        print("  python initialize_schema.py")
        print("\nOr manually via psql:")
        print("  psql <your-connection-string> -f sql/00_setup.sql")
    else:
        print("\n✅ Schema already initialized!")
        print("   Your database is ready to use.")
    
    print("\n" + "="*70)
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("  • Verify your connection string is correct")
    print("  • Check if database server is running")
    print("  • Verify network connectivity")
    print("  • Check credentials are valid")
    sys.exit(1)
