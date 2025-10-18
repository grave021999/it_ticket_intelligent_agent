from fastapi import FastAPI
import requests

app = FastAPI(title="MCP Layer for IT Ticket API")
API_BASE = "http://localhost:8000"

@app.get("/")
def root():
    return {"message": "✅ MCP server is running and connected to FastAPI backend"}

@app.get("/mcp/get_ticket_count")
def get_ticket_count():
    return requests.get(f"{API_BASE}/tickets/count").json()

@app.get("/mcp/get_ticket/{ticket_id}")
def get_ticket(ticket_id: str):
    return requests.get(f"{API_BASE}/tickets/{ticket_id}").json()

@app.get("/mcp/get_tickets_by_status/{status}")
def get_tickets_by_status(status: str):
    return requests.get(f"{API_BASE}/tickets/status/{status}").json()

@app.get("/mcp/get_tickets_by_category/{category}")
def get_tickets_by_category(category: str):
    return requests.get(f"{API_BASE}/tickets/category/{category}").json()

@app.get("/mcp/get_tickets_by_priority/{priority}")
def get_tickets_by_priority(priority: str):
    return requests.get(f"{API_BASE}/tickets/priority/{priority}").json()

@app.get("/mcp/get_tickets_by_creator/{user}")
def get_tickets_by_creator(user: str):
    return requests.get(f"{API_BASE}/tickets/creator/{user}").json()

@app.get("/mcp/get_tickets_by_assignee/{user}")
def get_tickets_by_assignee(user: str):
    return requests.get(f"{API_BASE}/tickets/assignee/{user}").json()

@app.get("/mcp/get_recent_tickets/{days}")
def get_recent_tickets(days: int):
    return requests.get(f"{API_BASE}/tickets/recent/{days}").json()
