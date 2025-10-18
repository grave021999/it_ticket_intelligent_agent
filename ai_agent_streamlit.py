
import streamlit as st
import requests
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# ✅ Must be the first Streamlit command
# ------------------------------------------------------------------------------
st.set_page_config(page_title="IT Ticket AI Agent", page_icon="🤖", layout="wide")

# ------------------------------------------------------------------------------
# 🧩 Load environment variables
# ------------------------------------------------------------------------------
load_dotenv()

# ------------------------------------------------------------------------------
# 🔐 Safely get secrets from Streamlit or .env
# ------------------------------------------------------------------------------
def get_secret(key: str, default: str = None):
    """Safely read a value from st.secrets (if available) or from environment."""
    try:
        if "st" in globals() and hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# ------------------------------------------------------------------------------
# 🌐 Backend service URLs
# ------------------------------------------------------------------------------
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
MCP_BASE = get_secret("MCP_BASE", "http://localhost:9000/mcp")
A2A_BASE = get_secret("A2A_BASE", "http://localhost:9100/a2a")
API_BASE = get_secret("API_BASE", "http://localhost:8000")

# ------------------------------------------------------------------------------
# 🧠 Validate and initialize OpenAI client
# ------------------------------------------------------------------------------
if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith("sk-"):
    st.error("❌ Invalid or missing OpenAI API key. Please verify `.env` or Streamlit Secrets.")
    st.stop()

try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    st.success("✅ OpenAI client initialized successfully!")
except Exception as e:
    st.error(f"⚠️ Failed to initialize OpenAI client: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# 🧩 Core logic functions
# ------------------------------------------------------------------------------

def handle_query(query: str):
    """Interpret user question, fetch from MCP, and summarize result."""
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

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        )
        plan = json.loads(completion.choices[0].message.content.strip())
        endpoint = plan.get("endpoint")
        if not endpoint:
            return "❌ This doesn’t match any known ticket dataset field."
    except Exception as e:
        return f"⚠️ Could not interpret question: {e}"

    # Call the MCP API
    try:
        response = requests.get(f"{MCP_BASE}{endpoint}")
        if response.status_code != 200:
            return f"⚠️ MCP API Error: {response.status_code} - {response.text}"
        data = response.json()
    except Exception as e:
        return f"⚠️ Error calling MCP API: {e}"

    # Summarize the API response
    summary_prompt = f"""
    The user asked: {query}
    Endpoint used: {endpoint}
    API response: {json.dumps(data, indent=2)}
    Write a concise, human-friendly markdown summary.
    """
    try:
        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarize IT ticket data clearly."},
                {"role": "user", "content": summary_prompt},
            ],
        )
        return final.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error summarizing response: {e}"


def ask_data_agent(question: str):
    """Handles A2A queries sent to the secondary DataAgent server."""
    try:
        res = requests.get(f"{A2A_BASE}/query", params={"question": question})
        if res.status_code == 200:
            data = res.json()
            return data.get("final_answer", "No response from DataAgent.")
        else:
            return f"⚠️ DataAgent error: {res.status_code}"
    except Exception as e:
        return f"⚠️ A2A communication failed: {e}"

# ------------------------------------------------------------------------------
# 🎨 Streamlit UI
# ------------------------------------------------------------------------------

st.markdown("<h1 style='text-align: center;'>🤖 IT Ticket AI Agent</h1>", unsafe_allow_html=True)
st.markdown("Ask questions about your IT tickets below:")

query = st.text_input(
    "💬 Enter your question:",
    placeholder="e.g., Show open tickets or show tickets assigned to Michael",
)

if st.button("Submit"):
    if not query.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("🤔 Thinking..."):
            if query.lower().startswith("ask data agent"):
                question = query.replace("ask data agent", "").strip()
                response = ask_data_agent(question)
            else:
                response = handle_query(query)

        st.markdown("### 💡 Response")
        st.markdown(response.replace("\n", "  \n"), unsafe_allow_html=True)
