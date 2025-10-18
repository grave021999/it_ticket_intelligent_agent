import os
import json
import requests
from openai import OpenAI

MCP_BASE = "http://localhost:9000/mcp"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def handle_query(query: str):
    system_prompt = """
    You are an intelligent IT Ticket Data Agent.
    You access an MCP layer with endpoints like:
    /get_ticket_count, /get_ticket/{id}, /get_tickets_by_status/{status},
    /get_tickets_by_category/{category}, /get_tickets_by_creator/{user},
    /get_tickets_by_assignee/{user}, /get_tickets_by_priority/{priority},
    /get_recent_tickets/{days}.
    Each record includes: ticket_id, title, description, category, subcategory,
    status, priority, created_by, assigned_to, created_date.
    Interpret user questions, extract parameters, and reply only in JSON:
    {"endpoint": "...", "summary": "..."}.
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )

    try:
        plan = json.loads(completion.choices[0].message.content.strip())
    except Exception:
        return "⚠️ I couldn’t interpret that question correctly. Try rephrasing."

    endpoint = plan.get("endpoint")
    if not endpoint:
        return "❌ This doesn’t match any known ticket dataset field."

    try:
        response = requests.get(f"{MCP_BASE}{endpoint}").json()
    except Exception as e:
        return f"⚠️ Error calling MCP API: {e}"

    summary_prompt = f"""
    The user asked: {query}
    Endpoint used: {endpoint}
    API response: {json.dumps(response, indent=2)}
    Write a concise, human-friendly summary.
    """

    final = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize IT ticket data clearly."},
            {"role": "user", "content": summary_prompt}
        ]
    )

    return final.choices[0].message.content


def ask_data_agent(question: str):
    try:
        res = requests.get("http://localhost:9100/a2a/query", params={"question": question})
        return res.json().get("final_answer", "No response from DataAgent.")
    except Exception as e:
        return f"⚠️ A2A communication failed: {e}"


def main():
    print("🤖 IT Ticket Agent ready!")
    print("Ask me anything about your dataset, for example:")
    print("- Who created ticket TCK-b8603b46?")
    print("- What’s the status of ticket TCK-8ac0b1ad?")
    print("- Show tickets assigned to Michael.")
    print("- Which tickets are still open?")
    print("- High priority tickets from last 3 days.")
    print("- You can also say: 'ask data agent show open tickets'")
    print("- exit\n")

    while True:
        user_input = input("👉 Your question: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        if user_input.lower().startswith("ask data agent"):
            question = user_input.replace("ask data agent", "").strip()
            print("🤝 A2A:", ask_data_agent(question), "\n")
            continue

        print("\n💬 Thinking...\n")
        print("💡", handle_query(user_input), "\n")


if __name__ == "__main__":
    main()
