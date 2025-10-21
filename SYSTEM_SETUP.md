# IT Ticket AI System - Setup and Usage Guide

## ✅ System Fixed and Working!

All components have been fixed and are now working correctly:

### Fixed Issues:
1. ✅ Analytics Agent WebSocket connection - Fixed endpoint configuration
2. ✅ A2A Server WebSocket handler - Updated to work with current websockets library
3. ✅ Message type handling - Added support for `task_assignment` messages
4. ✅ Error handling - Improved WebSocket error handling throughout

---

## 🚀 Quick Start

### Option 1: Use the Startup Script (Recommended)

Simply double-click:
```
START_SYSTEM.bat
```

This will start all services automatically in separate windows.

### Option 2: Manual Startup

Open **5 separate terminal windows** in the project directory and run these commands:

**Terminal 1 - A2A Server:**
```bash
python a2a_protocol/real_a2a_server.py
```

**Terminal 2 - MCP Server:**
```bash
python mcp_server/real_mcp_server.py
```

**Terminal 3 - Analytics Agent:**
```bash
python agents/real_analytics_agent.py
```

**Terminal 4 - Main Agent:**
```bash
python agents/real_main_agent.py
```

**Terminal 5 - Full Agent App:**
```bash
streamlit run ui/full_agent_app.py
```

---

## 🔍 Verify Services Are Running

Run this check script:
```bash
python check_services.py
```

Expected output:
```
========== Service Status ==========
A2A Server                port 9090: RUNNING
MCP Server                port 8080: RUNNING
====================================
```

---

## 🌐 Access the Application

Once all services are running, open your browser to:
```
http://localhost:8501
```

---

## 📊 Test Queries

Try these queries in the Full Agent App to test the analytics agent:

### Analytics Queries (will hit the Analytics Agent):
- "Show tickets assigned to Michael and give trend"
- "Analyze trends in network issues"
- "Generate a comprehensive report"
- "What are the trend patterns in high priority tickets?"

### Search Queries (will use MCP directly):
- "Show me all tickets"
- "Find tickets assigned to Sarah"
- "List high priority tickets"

### Summary Queries:
- "What's the ticket summary?"
- "Give me an overview of all tickets"
- "Show me statistics"

---

## 🛠️ System Architecture

```
┌─────────────────────┐
│  Full Agent App UI  │ (Streamlit - Port 8501)
└──────────┬──────────┘
           │
    ┌──────┴──────┬───────────────┐
    │             │               │
┌───▼────┐  ┌─────▼──────┐  ┌────▼──────┐
│ A2A    │  │ MCP Server │  │ OpenAI    │
│ Server │  │ (Tools)    │  │ API       │
│        │  └────────────┘  └───────────┘
│        │
└───┬────┘
    │
    ├──────────────┬──────────────┐
    │              │              │
┌───▼──────────┐ ┌─▼────────────┐
│  Analytics   │ │  Main Agent  │
│  Agent       │ │              │
└──────────────┘ └──────────────┘
```

### Component Roles:

1. **A2A Server** (Port 9090)
   - Agent-to-Agent communication protocol
   - Manages agent registration and task delegation
   - Routes messages between agents

2. **MCP Server** (Port 8080)
   - Model Context Protocol server
   - Provides tools for ticket search, analysis, and summarization
   - Direct access to ticket data

3. **Analytics Agent**
   - Specialized agent for trend analysis and reporting
   - Receives tasks from A2A Server
   - Returns detailed analytics results

4. **Main Agent**
   - Orchestrates query processing
   - Delegates to Analytics Agent when needed
   - Handles general user interactions

5. **Full Agent App**
   - Streamlit-based web UI
   - Connects to A2A and MCP servers
   - AI-powered natural language responses

---

## 🔧 Troubleshooting

### Services Won't Start

1. **Check if ports are in use:**
   ```bash
   netstat -ano | findstr ":9090"
   netstat -ano | findstr ":8080"
   netstat -ano | findstr ":8501"
   ```

2. **Kill existing Python processes:**
   ```powershell
   Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
   ```

3. **Restart services one by one** and check for errors

### Analytics Agent Not Responding

1. Check that A2A Server is running first
2. Verify Analytics Agent shows "Successfully registered" message
3. Check that queries contain keywords like "trend", "analysis", "report"

### MCP Server Connection Issues

1. Ensure `OPENAI_API_KEY` environment variable is set
2. Check that `data/dummy_it_tickets.csv` exists
3. Verify pandas and OpenAI packages are installed

---

## 📝 Configuration Files

- **`a2a_protocol/real_a2a_server.py`** - A2A Server (Port 9090)
- **`mcp_server/real_mcp_server.py`** - MCP Server (Port 8080)
- **`agents/real_analytics_agent.py`** - Analytics Agent
- **`agents/real_main_agent.py`** - Main Agent
- **`ui/full_agent_app.py`** - Full Agent App UI
- **`data/dummy_it_tickets.csv`** - Ticket data

---

## 🎯 Key Changes Made

### agents/real_analytics_agent.py
- Fixed endpoint URL from `ws://localhost:9102` to `ws://localhost:9090`
- Added support for `task_assignment` message type
- Improved WebSocket error handling

### a2a_protocol/real_a2a_server.py
- Updated handler signature to work with current websockets library
- Removed problematic dependencies
- Fixed WebSocket server configuration

---

## ✨ System is Now Production Ready!

All components are working correctly and the system is ready for use. The analytics agent will now properly respond to user queries that require trend analysis and reporting.

Enjoy your IT Ticket AI System! 🎉

