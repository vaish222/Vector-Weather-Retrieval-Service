"""
Script to create a Lakebase instance for Weather Retrieval Service
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import DatabaseSize

w = WorkspaceClient()

# Create a Lakebase project
project = w.postgres.projects.create(
    name="weather-retrieval-db",
    region="us-west-2",  # Change to your region
    size=DatabaseSize.SMALL  # SMALL, MEDIUM, or LARGE
)

print(f"✓ Lakebase project created: {project.name}")
print(f"  Project ID: {project.id}")
print(f"  Status: {project.status}")

# Create the main branch
branch = w.postgres.branches.create(
    project_name=project.name,
    branch_name="main"
)

print(f"\n✓ Branch created: {branch.branch_name}")
print(f"  Branch ID: {branch.id}")

# Get the connection endpoint
endpoint = w.postgres.endpoints.get(
    project_name=project.name,
    branch_name="main"
)

print(f"\n✓ Endpoint ready!")
print(f"  Host: {endpoint.host}")
print(f"  Port: {endpoint.port}")
print(f"  Database: {endpoint.database}")

# The connection string format
conn_string = f"postgresql://<username>:<password>@{endpoint.host}:{endpoint.port}/{endpoint.database}"
print(f"\n📝 Connection String Template:")
print(f"   {conn_string}")
print(f"\n   Replace <username> and <password> with your Databricks credentials")
