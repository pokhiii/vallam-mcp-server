import os
import json
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

app = FastMCP()
CORE_APP_URL = os.getenv("CORE_APP_URL")
SERVICE_AUTH_TOKEN = os.getenv("SERVICE_AUTH_TOKEN")

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


# ---- MCP TOOL 1: search ----
@app.tool("search")
def search(query: str):
    """
    Handle user search queries like:
    "find struggling students of class 3rd in math"
    """
    # You can add simple pattern extraction here
    # For now, assume class_id=3, subject="math"
    data = get_struggling_students(class_id=3, subject="math", period="this_month")

    results = []
    for s in data.get("students", []):
        results.append({
            "id": str(s["id"]),
            "title": s["name"],
            "url": f"/students/{s['id']}"
        })

    # The search tool must return a JSON string under content → type=text
    return {
        "content": [{
            "type": "text",
            "text": json.dumps({"results": results})
        }]
    }


# ---- MCP TOOL 2: fetch ----
@app.tool("fetch")
def fetch(student_id: str):
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
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({"error": f"Failed to fetch student: {str(e)}"})
            }]
        }

    doc = {
        "id": student_id,
        "title": student["name"],
        "text": json.dumps(student),
        "url": f"/students/{student_id}"
    }

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(doc)
        }]
    }


if __name__ == "__main__":
    app.run(transport="http", host="0.0.0.0", port=8010)
