import os
import json
import requests
import uvicorn
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
        if not CORE_APP_URL:
            return {"error": "CORE_APP_URL not configured", "students": []}
        
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
    except requests.exceptions.RequestException as e:
        return {"error": f"Core app unavailable: {str(e)}", "students": []}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "students": []}


@rest_app.post("/mcp/search")
async def rest_search(request: SearchRequest):
    try:
        result = search_logic(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rest_app.get("/mcp/fetch/{student_id}")
async def rest_fetch(student_id: str):
    try:
        result = fetch_logic(student_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rest_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vallam-mcp-server"}

def extract_params_from_query(query: str):
    """Extract class_id, subject, and period from natural language query."""
    import re
    
    query_lower = query.lower()
    
    class_match = re.search(r'(?:class|grade)\s*(\d+)(?:th|st|nd|rd)?', query_lower)
    if not class_match:
        class_match = re.search(r'(\d+)(?:th|st|nd|rd)?\s*(?:class|grade)', query_lower)
    class_id = class_match.group(1) if class_match else None
    
    subjects = ["math", "english", "science", "history", "geography", "physics", "chemistry", "biology"]
    subject = None
    for subj in subjects:
        if subj in query_lower:
            subject = subj
            break
    
    period = None
    if "this month" in query_lower:
        period = "this_month"
    elif "last month" in query_lower:
        period = "last_month"
    elif "this year" in query_lower:
        period = "this_year"
    elif "last year" in query_lower:
        period = "last_year"
    
    return class_id, subject, period

def search_logic(query: str):
    """
    Handle user search queries like:
    "find struggling students of class 7 in math this month"
    """
    class_id, subject, period = extract_params_from_query(query)
    
    if not class_id or not subject:
        return {
            "results": [],
            "error": f"Could not extract required parameters from query. Found: class_id={class_id}, subject={subject}",
            "hint": "Try: 'find struggling students of class 7 in math this month'"
        }
    
    data = get_struggling_students(class_id=class_id, subject=subject, period=period or "")

    if "error" in data:
        return {"results": [], "error": data["error"]}

    students_list = data.get("students", [])
    
    results = []
    for s in students_list:
        student_name = s.get("name", "Unknown")
        score = s.get("score", "N/A")
        date = s.get("date", "N/A")
        
        results.append({
            "name": student_name,
            "class": s.get("class_id"),
            "subject": s.get("subject"),
            "score": score,
            "date": date,
            "url": f"/students/{student_name.replace(' ', '_')}"
        })

    return {
        "results": results,
        "query_params": {
            "class_id": class_id,
            "subject": subject,
            "period": period
        },
        "total_students": len(results)
    }

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
    uvicorn.run(rest_app, host="0.0.0.0", port=8010)