import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

rest_app = FastAPI(title="Vallam MCP REST API", version="1.0.0")
mcp_app = FastMCP()

# Add CORS middleware
rest_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
CORE_APP_URL = os.getenv("CORE_APP_URL")
SERVICE_AUTH_TOKEN = os.getenv("SERVICE_AUTH_TOKEN")

# Request models for REST API
class SearchRequest(BaseModel):
    query: str
    variables: dict = {}

# ---- Helper to call Django safely ----
def get_struggling_students(class_id, subject, period):
    """Query the core Django app for struggling students."""
    try:
        resp = requests.get(
            f"{CORE_APP_URL}/api/v1/assistant/students/struggling",
            params={
                "class_id": class_id,
                "subject": subject,
                "period": period,
            },
            headers={"Authorization": f"Bearer {SERVICE_AUTH_TOKEN}"},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"Core app unavailable: {str(e)}"}


# ---- REST API ENDPOINTS ----
@rest_app.post("/mcp/search")
async def rest_search(request: SearchRequest):
    """REST endpoint for search queries"""
    try:
        result = search_logic(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rest_app.get("/mcp/fetch/{student_id}")
async def rest_fetch(student_id: str):
    """REST endpoint to fetch student details"""
    try:
        result = fetch_logic(student_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rest_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vallam-mcp-server"}

# ---- SHARED LOGIC ----
def search_logic(query: str):
    """
    Handle user search queries like:
    "find struggling students of class 3rd in math"
    """
    # You can add simple pattern extraction here
    # For now, assume class_id=3, subject="math"
    data = get_struggling_students(class_id=7, subject="math", period="last_month")

    results = []
    for s in data.get("students", []):
        results.append({
            "id": str(s["id"]),
            "title": s["name"],
            "url": f"/students/{s['id']}"
        })

    return {"results": results}

def fetch_logic(student_id: str):
    """Fetch full student report for a given student ID."""
    try:
        resp = requests.get(
            f"{CORE_APP_URL}/api/v1/assistant/student/{student_id}/report",
            headers={"Authorization": f"Bearer {SERVICE_AUTH_TOKEN}"},
            timeout=5,
        )
        resp.raise_for_status()
        student = resp.json()
    except Exception as e:
        return {"error": f"Failed to fetch student: {str(e)}"}

    return {
        "id": student_id,
        "title": student["name"],
        "data": student,
        "url": f"/students/{student_id}"
    }

# ---- MCP TOOLS ----
@mcp_app.tool("search")
def mcp_search(query: str):
    """MCP tool for search queries"""
    result = search_logic(query)
    return {
        "content": [{
            "type": "text",
            "text": json.dumps(result)
        }]
    }

@mcp_app.tool("fetch")
def mcp_fetch(student_id: str):
    """MCP tool to fetch student details"""
    result = fetch_logic(student_id)
    return {
        "content": [{
            "type": "text",
            "text": json.dumps(result)
        }]
    }

if __name__ == "__main__":
    import uvicorn
    # Run the REST API server
    uvicorn.run(rest_app, host="0.0.0.0", port=8010)