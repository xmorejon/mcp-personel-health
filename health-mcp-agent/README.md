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

---

## Architecture & How It Works

### End-to-End Data Flow

```
Google Fit / Google Drive
       │  (separate backend pipeline)
       ▼
  Firestore DB
  (health_metrics collection)
       │
       ▼
┌─────────────────────────────────────────────────┐
│           Cloud Run: health-mcp-agent            │
│                                                 │
│  ┌─────────────┐      ┌────────────────────┐    │
│  │  FastAPI     │      │  FastMCP Server    │    │
│  │  Web Server  │      │  mounted at /mcp   │    │
│  └──────┬──────┘      └────────────────────┘    │
│         │  (internal call)          ▲             │
│         ▼                           │             │
│  ┌─────────────┐    ┌──────────────┴─────────┐  │
│  │  ADK Agent  │───▶│  McpToolset Client     │  │
│  │  (HealthMate│    │  (StreamableHTTP /mcp) │  │
│  │  Gemini 2.5 │    └────────────────────────┘  │
│  │  Flash)     │                                 │
│  └─────────────┘                                 │
└─────────────────────────────────────────────────┘
         ▲
         │  HTTPS + Google ID Token
         ▼
  Browser Chat UI
  (Google Sign-In via GSI)
```

The entire stack — web UI, API, MCP server, and AI agent — runs in a **single Cloud Run service**.

---

### Authentication Flow

1. The user opens the app and signs in with **Google Sign-In (GSI)**.
2. Google returns an **ID token** (JWT) confirming the user's identity.
3. Every chat request sends this token in the `Authorization: Bearer` header.
4. The server validates the token against `https://oauth2.googleapis.com/tokeninfo`.
5. The email is checked against an internal whitelist (`USER_MAPPING` in `main.py`).
6. The email maps to an internal user ID (e.g., `user_001`) used to scope Firestore access.

---

### MCP Tools Available

The agent has access to **3 read-only MCP tools** defined in `health_tools.py`, all querying the `health_metrics` Firestore collection (most recent document, ordered by `date` descending):

| Tool | Description |
|---|---|
| `get_latest_vitals` | Returns `averageHeartRate`, `steps`, `weight`, and `date` from the latest record |
| `get_activities` | Returns the latest recorded activities (WALKING, RUNNING, etc.) with distance, duration, and time of day |
| `get_health_summary` | Returns all fields from the latest Firestore document as a complete health summary |

> **Read-only by design.** The agent can never write, modify, or delete any data.

---

### The AI Agent (HealthMate)

- **Model:** Gemini 2.5 Flash via **Vertex AI** (using Application Default Credentials)
- **Framework:** Google Agent Development Kit (ADK) with `InMemorySessionService`
- **Persona:** Warm, conversational personal health companion — optimised for voice-assistant style output (no markdown, short sentences)
- **Security:** Built-in prompt injection protection in the system prompt; strictly refuses out-of-scope requests

---

### Google Cloud Services Used

| Service | Role |
|---|---|
| **Cloud Run** | Hosts the entire application (UI + API + MCP server + agent) |
| **Firestore** | Stores daily health metrics — the source of truth |
| **Vertex AI (Gemini 2.5 Flash)** | Powers natural language understanding and response generation |
| **Google OAuth / tokeninfo API** | Validates user identity on every request |
| **FastMCP** | Implements the MCP protocol server exposing the 3 health tools |
| **Google ADK** | Orchestrates the agent loop (LLM ↔ tools ↔ response) |

---

### Key Configuration

| Environment Variable | Purpose |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth client ID for Google Sign-In validation |
| `PROJECT_ID` | GCP project ID (`mcp-personel-health`) |
| `FIRESTORE_MCP_ENDPOINT` | URL of the MCP server (`/mcp/mcp`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to `1` to use Vertex AI instead of Gemini API key |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI routing |
| `GOOGLE_CLOUD_LOCATION` | Set to `global` for Gemini 2.5+ model availability |

---

### Production URL

```
https://health-mcp-agent-600671868745.europe-west3.run.app
```
