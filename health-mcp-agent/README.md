# Health MCP Agent

This project exposes a stateless FastAPI HTTP webhook that powers a Health Information Agent using the Google Agent Development Kit (ADK). It connects to a Firestore MCP endpoint in a read-only capacity to ensure health data safety.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
3. Run the development server:
   ```bash
   uvicorn main:app --reload --port 8080
   ```

## Usage

Send a POST request to `http://localhost:8080/`:
```json
{
  "query": "What are my recent lab results?",
  "userId": "user123"
}
```

## Deployment

Build and deploy to Google Cloud Run:
```bash
gcloud run deploy health-mcp-agent --source . --project mcp-personel-health
```
