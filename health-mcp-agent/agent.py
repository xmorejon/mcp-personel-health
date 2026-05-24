from google.auth import default

# Assuming google-genai provides Agent and McpToolset
try:
    from google.genai.agents import Agent, McpToolset
except ImportError:
    # Fallback generic imports
    from google_adk import Agent, McpToolset

from config import PROJECT_ID, MODEL_NAME, FIRESTORE_MCP_ENDPOINT
from prompts import SYSTEM_PROMPT

def get_agent() -> Agent:
    """Initialize and return the ADK Agent."""
    credentials, project_id = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    
    # Configure the MCP Toolset pointing to the Remote MCP endpoint
    # Tool filter enforces read-only operations for health data safety
    mcp_toolset = McpToolset(
        endpoint=FIRESTORE_MCP_ENDPOINT,
        credentials=credentials,
        tool_filter=["get_document", "list_documents", "list_collections"]
    )
    
    # Initialize the Agent
    agent = Agent(
        model=MODEL_NAME,
        system_prompt=SYSTEM_PROMPT,
        tools=[mcp_toolset]
    )
    
    return agent
