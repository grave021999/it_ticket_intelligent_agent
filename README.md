🧠 IT Ticket Intelligent Agent System

A complete AI-powered IT Helpdesk Ticket System built using FastAPI, Streamlit, and OpenAI GPT models, with modular microservices for reasoning, querying, and visualizing IT ticket data.

It lets users query helpdesk tickets using natural language —
for example:

“Show open network tickets”
“List high-priority tickets assigned to Michael”

The system automatically interprets, fetches, and summarizes the results through a connected API and LLM reasoning layer.

🚀 Features

💬 Natural language querying of IT ticket data

🧩 Layered microservice design with a middleware (MCP) between AI and backend

📊 Auto-generated ticket dataset using Faker

⚡ FastAPI backend for structured ticket APIs

🤖 GPT-powered query reasoning and data summarization

🔄 Agent-to-Agent (A2A) communication for multi-agent collaboration

🌐 Streamlit web UI for an interactive experience

🧠 CLI mode for command-line interaction

🏗️ System Architecture
                        ┌───────────────────────────┐
                        │        User Query         │
                        └────────────┬──────────────┘
                                     │
                                     ▼
               🤖 AI Agent (ai_agent.py / ai_agent_streamlit.py)
                             │
      ┌──────────────────────┴───────────────────────────┐
      │                                                  │
      ▼                                                  ▼
MCP Layer (mcp_server.py)                   Data Agent (a2a_server.py)
      │                                                  │
      ▼                                                  │
FastAPI Backend (main.py)                                │
      │                                                  │
      ▼                                                  │
Ticket Dataset (dummy_it_tickets.csv)  ◄─────────────────┘

📁 Project Structure
it_ticket_project/
│
├── ai_agent.py              # Main CLI-based AI Agent
├── ai_agent_streamlit.py    # Streamlit Web UI version of AI Agent
├── a2a_server.py            # Optional Data Agent (supports inter-agent logic)
├── mcp_server.py            # Middleware between AI and backend
├── main.py                  # FastAPI backend for IT ticket dataset
├── tickets_data.py          # Generates dummy ticket data using Faker
├── dummy_it_tickets.csv     # Auto-generated dataset
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md                # Documentation

⚙️ Setup & Installation
1️⃣ Clone the Repository
git clone https://github.com/yourusername/it_ticket_project.git
cd it_ticket_project

2️⃣ Create a Virtual Environment
python -m venv venv
venv\Scripts\activate      # On Windows
# or
source venv/bin/activate   # On Mac/Linux

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Create a .env File
# .env
OPENAI_API_KEY=sk-your-openai-key
API_BASE=http://localhost:8000
MCP_BASE=http://localhost:9000/mcp
A2A_BASE=http://localhost:9100/a2a
ENV=development

▶️ Running the System

Run each service in a separate terminal window in the following order:

🧩 Step 1 — Generate Dummy Ticket Dataset
python tickets_data.py

🧠 Step 2 — Start the FastAPI Backend
uvicorn main:app --reload --port 8000

🔗 Step 3 — Start the MCP Server
uvicorn mcp_server:app --reload --port 9000

🤝 Step 4 (Optional) — Start the Data Agent
uvicorn a2a_server:app --reload --port 9100

💻 Step 5a — Run the CLI Agent
python ai_agent.py

🌐 Step 5b — Run the Streamlit Web Interface
streamlit run ai_agent_streamlit.py


Then open your browser at http://localhost:8501

💡 Example Queries

Try these examples (works in both CLI & Streamlit):

show open tickets
high priority tickets
show tickets assigned to Michael
who created ticket TCK-b8603b46
tickets created by Sarah
ask data agent show open tickets

🔍 How It Works

The user enters a natural language query.

The AI Agent uses GPT-4o-mini to decide which MCP API endpoint to call.

The MCP Layer routes the request to the backend API.

The FastAPI backend filters and retrieves data from the CSV dataset.

The AI Agent then summarizes and formats the result in natural English (Markdown).

Optionally, the query can be delegated to a Data Agent for multi-agent reasoning.

🌐 Streamlit Web Interface Preview

Input your query directly into the text box.

Responses are shown in structured Markdown (with ticket count and examples).

Works exactly like the CLI — powered by the same OpenAI logic and MCP API calls.

🧩 Tech Stack
Component	Technology
Language	Python 3.9+
Backend Framework	FastAPI
Web UI	Streamlit
AI Model	OpenAI GPT-4o-mini
Data Layer	Pandas
Dataset Generator	Faker
API Server	Uvicorn
Config Management	python-dotenv
HTTP Requests	requests
🧾 License

This project is for educational and demonstration purposes only.
All API keys and local data must be kept private and not shared publicly.