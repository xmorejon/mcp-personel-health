from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agent import get_agent
from health_tools import mcp

app = FastAPI(title="Health MCP Agent")
app.mount("/mcp", mcp.streamable_http_app())
security = HTTPBearer()

USER_MAPPING = {
    "xaviermorejonbalta@gmail.com": "user_001"
}

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# Initialize agent and runner once at startup
agent = get_agent()
session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name="health-mcp-agent",
    session_service=session_service
)

async def verify_google_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    data = response.json()
    if "error" in data or int(data.get("expires_in", 0)) <= 0:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = data.get("email")
    if email not in USER_MAPPING:
        raise HTTPException(status_code=401, detail="User not authorized")

    return email

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/ask", response_model=QueryResponse)
async def handle_query(
    request: QueryRequest,
    email: str = Depends(verify_google_token)
):
    try:
        user_id = USER_MAPPING.get(email)
        session = await session_service.create_session(
            app_name="health-mcp-agent",
            user_id=user_id
        )

        content = Content(parts=[Part(text=f"User ID: {user_id}\nQuery: {request.query}")])

        final_response = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content
        ):
            if event.is_final_response():
                final_response = event.message.parts[0].text
                break

        return QueryResponse(response=final_response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))