from google.auth import default
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams

from config import PROJECT_ID, MODEL_NAME, FIRESTORE_MCP_ENDPOINT
from prompts import SYSTEM_PROMPT

def get_agent() -> Agent:
    """Initialize and return the ADK Agent."""
    credentials, project_id = default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    # Configure MCP Toolset pointing to Cloud Run MCP endpoint
    mcp_toolset = McpToolset(
        connection_params=StreamableHTTPServerParams(
            url=FIRESTORE_MCP_ENDPOINT,
            headers={
                "Authorization": f"Bearer {credentials.token}"
            }
        )
    )

    # Initialize the Agent
    agent = Agent(
        model=MODEL_NAME,
        name="health_agent",
        instruction=SYSTEM_PROMPT,
        tools=[mcp_toolset]
    )

    return agent