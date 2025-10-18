from fastapi import FastAPI
import pandas as pd
from datetime import datetime, timedelta
import os

print("🚀 Starting FastAPI IT Ticket API...")

app = FastAPI(title="IT Helpdesk Ticket API")
CSV_FILE = "dummy_it_tickets.csv"

try:
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found.")
    print(f"📂 Loading {CSV_FILE} ...")
    df = pd.read_csv(CSV_FILE)
    print(f"✅ Loaded {len(df)} records.")
except Exception as e:
    print("❌ Error loading dataset:", e)
    df = pd.DataFrame()

tickets = df.to_dict(orient="records")

@app.get("/")
def home():
    return {"message": "Welcome to the IT Ticket API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "total_tickets_loaded": len(tickets)}

@app.get("/tickets/count")
def count_tickets():
    return {"total_tickets": len(tickets)}

@app.get("/tickets/{ticket_id}")
def get_ticket_by_id(ticket_id: str):
    ticket = df[df["ticket_id"].astype(str).str.lower() == ticket_id.lower()]
    if ticket.empty:
        return {"error": f"Ticket {ticket_id} not found"}
    return {"ticket": ticket.to_dict(orient="records")[0]}

@app.get("/tickets/status/{status}")
def get_tickets_by_status(status: str):
    result = df[df["status"].str.lower() == status.lower()]
    return {"count": len(result), "tickets": result.to_dict(orient="records")}

@app.get("/tickets/category/{category}")
def get_tickets_by_category(category: str):
    result = df[df["category"].str.lower() == category.lower()]
    return {"count": len(result), "tickets": result.to_dict(orient="records")}

@app.get("/tickets/priority/{priority}")
def get_tickets_by_priority(priority: str):
    result = df[df["priority"].str.lower() == priority.lower()]
    return {"count": len(result), "tickets": result.to_dict(orient="records")}

@app.get("/tickets/creator/{user}")
def get_tickets_by_creator(user: str):
    result = df[df["created_by"].str.lower() == user.lower()]
    return {"count": len(result), "tickets": result.to_dict(orient="records")}

@app.get("/tickets/assignee/{user}")
def get_tickets_by_assignee(user: str):
    result = df[df["assigned_to"].str.lower() == user.lower()]
    return {"count": len(result), "tickets": result.to_dict(orient="records")}

@app.get("/tickets/recent/{days}")
def get_recent_tickets(days: int):
    cutoff = datetime.now() - timedelta(days=days)
    result = df[pd.to_datetime(df["created_date"], errors="coerce") >= cutoff]
    return {"count": len(result), "tickets": result.to_dict(orient="records")}
