from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import get_agent

app = FastAPI(title="Health MCP Agent")

class QueryRequest(BaseModel):
    query: str
    userId: str

class QueryResponse(BaseModel):
    response: str

# Initialize the agent once at startup
agent = get_agent()

@app.post("/", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Stateless HTTPS POST endpoint to process agent queries."""
    try:
        # Provide the user context and the query to the agent
        full_query = f"User ID: {request.userId}\nQuery: {request.query}"
        
        # Run the agent
        response = agent.run(full_query)
        
        return QueryResponse(response=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
