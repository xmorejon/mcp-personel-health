import os

PROJECT_ID = os.getenv("PROJECT_ID", "mcp-personel-health")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
FIRESTORE_MCP_ENDPOINT = os.getenv(
    "FIRESTORE_MCP_ENDPOINT",
    "https://health-mcp-agent-600671868745.europe-west3.run.app"
)