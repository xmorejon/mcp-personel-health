import json
from google.cloud import firestore
from mcp.server.fastmcp import FastMCP
from config import PROJECT_ID

# Initialize Firestore
db = firestore.Client(project=PROJECT_ID)

# Initialize FastMCP server
mcp = FastMCP("HealthServer", stateless_http=True)

def _get_latest_health_doc():
    """Helper to get the most recent health document."""
    # The documents are ordered by date (e.g. '2026-05-20')
    docs = db.collection("health_metrics").order_by("date", direction=firestore.Query.DESCENDING).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None

@mcp.tool()
def get_latest_vitals() -> str:
    """Returns the user's latest vitals including heart rate, weight, and steps."""
    doc = _get_latest_health_doc()
    if not doc:
        return "No health metrics found."
    
    vitals = {
        "date": doc.get("date"),
        "averageHeartRate": doc.get("averageHeartRate"),
        "steps": doc.get("steps"),
        "weight": doc.get("weight"),
        "lastUpdated": str(doc.get("lastUpdated")) if doc.get("lastUpdated") else None
    }
    return json.dumps(vitals, indent=2)

@mcp.tool()
def get_activities() -> str:
    """Returns the user's latest activity and exercise data."""
    doc = _get_latest_health_doc()
    if not doc:
        return "No health metrics found."
    
    activities = doc.get("activities", [])
    if not activities:
        return "No activities recorded for the latest date."
        
    return json.dumps({"date": doc.get("date"), "activities": activities}, indent=2)

@mcp.tool()
def get_health_summary() -> str:
    """Returns an overall health summary from the latest metrics."""
    doc = _get_latest_health_doc()
    if not doc:
        return "No health metrics found."
        
    # Return all data for a summary
    return json.dumps(doc, indent=2, default=str)
