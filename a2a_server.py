from fastapi import FastAPI, Query
import requests
import os
import json
from openai import OpenAI

app = FastAPI(title="A2A Data Agent")
MCP_BASE = "http://localhost:9000/mcp"

@app.get("/")
def root():
    return {"message": "🤖 DataAgent is ready for A2A queries"}

@app.get("/a2a/query")
def handle_a2a_query(question: str = Query(..., description="Natural language question from another agent")):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    reasoning_prompt = """
    You are DataAgent. You can access these endpoints:
    /get_ticket_count, /get_tickets_by_status/{status}, /get_tickets_by_category/{category},
    /get_tickets_by_priority/{priority}, /get_tickets_by_creator/{user},
    /get_tickets_by_assignee/{user}, /get_ticket/{ticket_id}, /get_recent_tickets/{days}.
    Read the question and return JSON like:
    {"endpoint": "/get_tickets_by_status/Open", "summary": "Fetch open tickets"}.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": reasoning_prompt},
            {"role": "user", "content": question},
        ],
    )

    try:
        plan = json.loads(completion.choices[0].message.content.strip())
        endpoint = plan.get("endpoint")
        summary = plan.get("summary")
    except Exception:
        return {"error": "Could not interpret question"}

    if not endpoint:
        return {"error": "No endpoint chosen"}

    try:
        res = requests.get(f"{MCP_BASE}{endpoint}")
        data = res.json()
    except Exception as e:
        return {"error": f"Error calling MCP: {e}"}

    summarize_prompt = f"""
    Summarize this API response in one or two sentences.
    Endpoint: {endpoint}
    Response: {json.dumps(data, indent=2)}
    """

    summary_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize the API response clearly."},
            {"role": "user", "content": summarize_prompt},
        ],
    )

    final_answer = summary_completion.choices[0].message.content.strip()

    return {
        "a2a_origin": "DataAgent",
        "endpoint_used": endpoint,
        "summary": summary,
        "final_answer": final_answer,
        "raw_data": data,
    }
