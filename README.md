# Vallam MCP Server

This repository contains the **Model Context Protocol (MCP)** server used to connect ChatGPT (or other LLM-based tools) with the **Vallam Django Core App**.  
It enables AI assistants to access organizational data such as student assessments, performance analytics, and teacher dashboards securely.

---

## 🧠 Overview

The MCP server exposes standard **MCP tools** (`search`, `fetch`) that ChatGPT can use to:
- Identify struggling students
- Retrieve student progress reports
- Query structured data from the Django-based core app

It’s built with:
- [FastMCP](https://pypi.org/project/fastmcp/) — lightweight MCP server framework  
- [FastAPI](https://fastapi.tiangolo.com/) — high-performance web API  
- [ngrok](https://ngrok.com/) — for secure HTTPS tunneling during local development  

---

## ⚙️ Setup Instructions (for new developers)

### 1. Clone the repository
```bash
git clone https://github.com/<your-org>/vallam-mcp-server.git
cd vallam-mcp-server
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

Create a `.env` file in the project root (copy `.env.example` if provided):

```bash
CORE_APP_URL=http://127.0.0.1:8000
SERVICE_AUTH_TOKEN=replace_with_your_django_api_token
```

> 📝 `CORE_APP_URL` points to the Django core app (dev or staging).  
> `SERVICE_AUTH_TOKEN` is an authentication token for the Django API.

---

## 🚀 Running the Server

Run the server in **HTTP transport mode**:
```bash
python server.py
```

Expected output:
```
FastMCP 2.13.x
Server URL: http://0.0.0.0:8010/mcp
Transport: HTTP
```

Verify it works:
```bash
curl -X POST http://127.0.0.1:8010/mcp/search   -H "Content-Type: application/json"   -d '{"query": "find struggling students"}'
```

---

## 🌐 Exposing via HTTPS (for ChatGPT)

Since ChatGPT requires a **public HTTPS endpoint**, use [ngrok](https://ngrok.com/):

### 1. Install and connect ngrok
```bash
brew install ngrok  # macOS
ngrok config add-authtoken <your_auth_token>
```

### 2. Expose the MCP server
```bash
ngrok http 8010
```

You’ll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8010
```

Use this HTTPS URL in ChatGPT:
```
https://abc123.ngrok.io/mcp
```

---

## 🤖 Adding the Connector in ChatGPT

1. Open **ChatGPT → Settings → Apps & Connectors → Create**
2. Select **Add Custom Connector**
3. Fill in:
   - **Name:** Vallam MCP Server  
   - **Description:** ChatGPT connector for Vallam's Django-based student system  
   - **MCP Server URL:** `https://abc123.ngrok.io/mcp`  
   - **Authentication:** No authentication  
4. ✅ Check “I understand and want to continue”
5. Click **Create**

---

## ✅ Health Check Endpoint

You can verify server status directly:
```bash
curl http://127.0.0.1:8010/health
```

Expected response:
```json
{"status": "ok", "server": "Vallam MCP", "transport": "http"}
```

---

## 📁 Project Structure

```
vallam-mcp-server/
│
├── server.py            # Main MCP server (FastMCP)
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment config
├── README.md            # This file
└── venv/                # Local virtual environment (excluded via .gitignore)
```

---

## 🧪 Common Issues

| Symptom | Likely Cause | Fix |
|----------|---------------|-----|
| `TypeError: 'FastMCP' object is not callable` | Tried `uvicorn server:app` | Run with `python server.py` instead |
| ChatGPT says “Unsafe URL” | Using free ngrok domain | Use a paid ngrok subdomain (`yourname.ngrok.io`) or deploy to Render |
| `/sse` 404 | FastMCP HTTP mode uses `/mcp`, not `/sse` | Use `/mcp` endpoint |
| OAuth-related 404s | ChatGPT checks by default | Safe to ignore |

---

## 👥 Maintainers

- **Owner:** Vallam AI Platform Team  
- **Contact:** ai@vallam.school  

---

## 🪪 License

MIT License © 2025 Vallam AI
