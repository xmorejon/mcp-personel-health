from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from config import GOOGLE_CLIENT_ID
from pydantic import BaseModel
import httpx
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agent import get_agent
from health_tools import mcp

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield

app = FastAPI(title="Health MCP Agent", lifespan=lifespan)
app.mount("/mcp", mcp.streamable_http_app())

@app.get("/", response_class=HTMLResponse)
async def chat_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html.replace("__GOOGLE_CLIENT_ID__", GOOGLE_CLIENT_ID))

security = HTTPBearer()

USER_MAPPING = {
    "xaviermorejonbalta@gmail.com": "user_001",
    "<EMAIL_ADDRESS>": "user_001"
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
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    email = data.get("email")
    if email not in USER_MAPPING:
        raise HTTPException(status_code=401, detail="User not authorized")

    return email

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/routes")
async def list_routes():
    result = []
    for r in app.routes:
        result.append({
            "path": getattr(r, "path", str(r)),
            "type": type(r).__name__,
            "methods": list(getattr(r, "methods", None) or [])
        })
    return {"routes": result}

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