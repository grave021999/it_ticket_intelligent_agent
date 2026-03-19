<img width="1280" height="579" alt="banner" src="https://github.com/user-attachments/assets/e4964701-9f03-4eba-ada1-b3052827b194" />
# 🎟️ IT Ticket AI System

A multi-agent AI system for intelligent IT ticket management with natural language processing, trend analysis, and automated insights.

---

## ✨ Features

- 🤖 **Multi-Agent Architecture** - Specialized AI agents for different tasks
- 📊 **Analytics Agent** - Real-time trend analysis and pattern detection
- 🗣️ **Natural Language Interface** - Conversational AI responses (no more JSON!)
- 🔄 **Agent-to-Agent Communication** - Seamless task delegation via A2A protocol
- 🛠️ **MCP Tools** - Model Context Protocol for ticket operations
- 🎯 **Intelligent Routing** - Queries automatically routed to the right agent

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- OpenAI API key (set as environment variable `OPENAI_API_KEY`)
- Required packages: `pip install -r requirements.txt`

### 2. Start the System

**Option A: PowerShell Script (Recommended)**
```powershell
.\START_ALL.ps1
```

**Option B: Manual Startup**
```powershell
# Start each service in order
Start-Process python -ArgumentList "a2a_protocol/real_a2a_server.py"
Start-Sleep -Seconds 2

Start-Process python -ArgumentList "mcp_server/real_mcp_server.py"
Start-Sleep -Seconds 2

Start-Process python -ArgumentList "agents/real_analytics_agent.py"
Start-Sleep -Seconds 2

Start-Process python -ArgumentList "agents/real_main_agent.py"
Start-Sleep -Seconds 2

Start-Process streamlit -ArgumentList "run ui/full_agent_app.py"
```

### 3. Access the Application

Open your browser to: **http://localhost:8501**

---

## 📋 System Architecture

```
┌─────────────────────────────────┐
│   Full Agent App (Streamlit)    │  ← User Interface
│        Port 8501                 │
└────────────┬────────────────────┘
             │
       ┌─────┴─────┬───────────────┐
       │           │               │
   ┌───▼────┐  ┌───▼─────┐  ┌─────▼──────┐
   │  A2A   │  │   MCP   │  │  OpenAI    │
   │ Server │  │  Server │  │    API     │
   │  9090  │  │  8080   │  └────────────┘
   └───┬────┘  └─────────┘
       │
    ┌──┴──────────────┐
    │                 │
┌───▼──────────┐  ┌──▼────────────┐
│  Analytics   │  │  Main Agent   │
│   Agent      │  │               │
└──────────────┘  └───────────────┘
```

### Components

1. **A2A Server (Port 9090)**
   - Agent-to-Agent communication protocol
   - Task delegation and status management
   - Agent registration and discovery

2. **MCP Server (Port 8080)**
   - Model Context Protocol implementation
   - Ticket search, analysis, and summarization tools
   - Direct access to ticket data

3. **Analytics Agent**
   - Specialized in trend analysis and pattern detection
   - Processes complex analytical queries
   - Returns detailed insights and recommendations

4. **Main Agent**
   - Query orchestration and routing
   - Handles general user interactions
   - Delegates to Analytics Agent when needed

5. **Full Agent App (Streamlit UI)**
   - Web-based user interface
   - Natural language query processing
   - AI-powered response conversion

---

## 🧪 Example Queries

### Analytics Queries (Uses Analytics Agent)
```
✅ "Show tickets assigned to Michael and give trend"
✅ "Analyze trends in network issues"
✅ "Generate a comprehensive report"
✅ "What patterns do you see in high priority tickets?"
✅ "Give me insight into hardware failures"
```

### Search Queries (Uses MCP Tools)
```
✅ "Show me all tickets"
✅ "Find tickets assigned to Sarah"
✅ "List high priority tickets"
✅ "Search for network-related issues"
```

### Summary Queries
```
✅ "What's the ticket summary?"
✅ "Give me an overview of all tickets"
✅ "Show me statistics"
```

---

## 📊 Example Response

**Query:** "Show tickets assigned to Michael and give trend"

**Response:**
```
📊 Analytics Agent Response

Based on my analysis of the tickets assigned to Michael, I've reviewed 150 tickets 
and discovered some interesting patterns.

The most notable trend is that network issues are on the rise - we're seeing about 
a 15% increase compared to previous periods. This is something we should pay attention 
to.

Looking at the categories, the top three areas are Network issues, Email problems, 
and Hardware-related requests. The priority distribution shows that 60% are Medium 
priority, 25% are High priority (needing immediate attention), and 15% are Low priority.

Here are my recommendations:

1. Focus on network infrastructure improvements - With the 15% increase in network 
   issues, we should investigate the root cause.

2. Consider additional email support resources - Email is a top category, so evaluate 
   if more support is needed.

3. Monitor hardware failure patterns - Keep an eye on hardware issues to identify 
   any patterns.

Let me know if you'd like me to dive deeper into any of these areas!
```

---

## 🔧 Troubleshooting

### Services Won't Start

```powershell
# Check if ports are in use
netstat -ano | findstr ":9090"
netstat -ano | findstr ":8080"

# Stop all Python processes
Get-Process python,streamlit -ErrorAction SilentlyContinue | Stop-Process -Force

# Restart services
.\START_ALL.ps1
```

### Connection Issues

- Ensure all services start in order (A2A → MCP → Agents → UI)
- Wait 2-3 seconds between starting each service
- Check that `OPENAI_API_KEY` environment variable is set

---

## 📁 Project Structure

```
it_tickets_project/
├── a2a_protocol/
│   └── real_a2a_server.py      # Agent-to-Agent server
├── agents/
│   ├── real_analytics_agent.py  # Analytics specialist
│   └── real_main_agent.py       # Main orchestrator
├── mcp_server/
│   └── real_mcp_server.py       # MCP tools server
├── ui/
│   └── full_agent_app.py        # Main Streamlit app
├── data/
│   └── dummy_it_tickets.csv     # Sample ticket data
├── START_ALL.ps1                # PowerShell startup script
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 📚 Additional Documentation

- **FINAL_SOLUTION.md** - Technical details of the complete solution
- **NATURAL_LANGUAGE_RESPONSE.md** - How natural language conversion works
- **QUICK_START_GUIDE.md** - Detailed startup instructions
- **SYSTEM_SETUP.md** - Comprehensive system setup guide

---

## 🛑 Stopping the System

```powershell
# Stop all services
Get-Process python,streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 🎯 Key Features Explained

### 1. Natural Language Processing
The system uses GPT-4o-mini to convert technical JSON responses into conversational, human-friendly explanations.

### 2. Intelligent Agent Routing
Queries containing keywords like "trend", "analysis", "pattern", or "insight" are automatically routed to the Analytics Agent.

### 3. Multi-Layer Fallback
If the Analytics Agent is unavailable, the system falls back to:
1. MCP trend analysis tools
2. MCP search tools
3. Direct AI response

### 4. Real-Time Analytics
The Analytics Agent processes queries in real-time and provides:
- Trend analysis
- Pattern detection
- Statistical summaries
- Actionable recommendations

---

## 💡 Tips

- Start queries with action words: "Show", "Analyze", "Find", "Generate"
- Be specific: "Network issues in Q4" vs "issues"
- Use natural language: Ask as you would ask a colleague
- Try different phrasings if results aren't what you expect

---

## 🎉 System Status

```
✅ Multi-Agent Architecture - Working
✅ Natural Language Responses - Working
✅ Analytics Agent - Working
✅ Task Delegation - Working
✅ Real-Time Analysis - Working
✅ Fallback Mechanisms - Working
```

---

## 📄 License

This project is for internal use and demonstration purposes.

---

## 🤝 Support

For issues or questions, refer to the documentation files or check the troubleshooting section above.

---

**Enjoy your intelligent IT ticket management system!** 🎊
