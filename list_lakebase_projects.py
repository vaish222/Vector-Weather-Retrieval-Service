"""
List existing Lakebase projects and get connection strings
"""

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("\n📋 Your Lakebase Projects:")
print("=" * 70)

try:
    projects = w.postgres.projects.list()
    
    if not projects:
        print("No Lakebase projects found.")
        print("\nCreate one using create_lakebase.py or via the UI.")
    else:
        for project in projects:
            print(f"\n✓ Project: {project.name}")
            print(f"  ID: {project.id}")
            print(f"  Region: {project.region}")
            print(f"  Status: {project.status}")
            
            # Get branches
            try:
                branches = w.postgres.branches.list(project_name=project.name)
                print(f"  Branches:")
                for branch in branches:
                    print(f"    • {branch.branch_name} ({branch.status})")
                    
                    # Get endpoint for this branch
                    try:
                        endpoint = w.postgres.endpoints.get(
                            project_name=project.name,
                            branch_name=branch.branch_name
                        )
                        
                        print(f"\n  📝 Connection String for '{branch.branch_name}':")
                        conn_str = f"postgresql://token:<your-access-token>@{endpoint.host}:{endpoint.port}/{endpoint.database}"
                        print(f"     {conn_str}")
                        
                    except Exception as e:
                        print(f"    (Endpoint not ready: {e})")
                        
            except Exception as e:
                print(f"  Could not list branches: {e}")
                
except Exception as e:
    print(f"Error: {e}")
    print("\nLakebase might not be available in your workspace.")
    print("Check with your admin or use the UI to create a project.")

print("\n" + "=" * 70)
print("\n💡 TIP: For authentication, you can use:")
print("   • Option 1: Databricks personal access token")
print("   • Option 2: OAuth token (recommended for apps)")
print("   • Option 3: Service principal credentials")
