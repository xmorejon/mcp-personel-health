import os

PROJECT_ID = os.getenv("PROJECT_ID", "mcp-personel-health")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.1-pro")
FIRESTORE_MCP_ENDPOINT = os.getenv("FIRESTORE_MCP_ENDPOINT", "https://firestore.googleapis.com/mcp")
