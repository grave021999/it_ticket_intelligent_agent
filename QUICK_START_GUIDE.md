# 🚀 Quick Start Guide - IT Ticket AI System

## ✅ System Status: FULLY WORKING!

All issues have been fixed. The analytics agent now properly communicates with the UI.

---

## 📋 Step-by-Step Startup

### 1. Open PowerShell in the Project Directory

```powershell
cd "C:\Users\Lenovo India\it_tickets_project"
```

### 2. Start All Services (5 Commands)

**Copy and paste these commands one by one:**

```powershell
# 1. Start A2A Server
Start-Process python -ArgumentList "a2a_protocol/real_a2a_server.py"
Start-Sleep -Seconds 2

# 2. Start MCP Server  
Start-Process python -ArgumentList "mcp_server/real_mcp_server.py"
Start-Sleep -Seconds 2

# 3. Start Analytics Agent
Start-Process python -ArgumentList "agents/real_analytics_agent.py"
Start-Sleep -Seconds 2

# 4. Start Main Agent
Start-Process python -ArgumentList "agents/real_main_agent.py"
Start-Sleep -Seconds 2

# 5. Start Full Agent App UI
Start-Process streamlit -ArgumentList "run ui/full_agent_app.py"
```

### 3. Verify Services are Running

```powershell
python check_services.py
```

Expected output:
```
========== Service Status ==========
A2A Server                port 9090: RUNNING
MCP Server                port 8080: RUNNING
====================================
```

### 4. Verify Analytics Agent

```powershell
python verify_analytics_agent.py
```

Expected output:
```
[OK] Connected to A2A Server
[OK] Discovered 1 agents:
  - Analytics Agent (analytics_agent)
[OK] Analytics Agent is registered and available!
[SUCCESS] Analytics Agent is working correctly!
```

---

## 🌐 Access the Application

The Full Agent App will automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, just navigate to that URL.

---

## 🧪 Test Analytics Queries

Try these queries to test the analytics agent integration:

### Analytics-Focused Queries (Will hit Analytics Agent):
```
✓ "Show tickets assigned to Michael and give trend"
✓ "Analyze trends in network issues"
✓ "Generate a comprehensive report"  
✓ "What are the trend patterns?"
✓ "Give me insight into high priority tickets"
```

### Regular Queries (Will use MCP directly):
```
✓ "Show me all tickets"
✓ "Find tickets assigned to Sarah"
✓ "What's the ticket summary?"
```

---

## 🔍 What Was Fixed

### Issue 1: Analytics Agent Not Responding ❌ → ✅
**Problem:** Agent was timing out after 5 seconds
**Solution:** 
- Changed UI to poll for task status instead of waiting for push notifications
- Increased timeout from 5 to 15 seconds
- Analytics agent now properly processes and responds to tasks

### Issue 2: WebSocket Handler ❌ → ✅
**Problem:** A2A server had WebSocket version compatibility issues
**Solution:** Updated handler signature to match current websockets library

### Issue 3: Message Type Handling ❌ → ✅
**Problem:** Analytics agent only handled `delegate_task` but server sent `task_assignment`
**Solution:** Added support for both message types

---

## 🛑 Stopping the System

To stop all services:

```powershell
Get-Process python,streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
```

---

## 📊 System Architecture

```
User Browser (http://localhost:8501)
         ↓
   Full Agent App (Streamlit)
         ↓
    ┌────┴────┐
    ↓         ↓
A2A Server  MCP Server
    ↓         ↓
    ↓    (Ticket Tools)
    ↓
 ┌──┴────────────┐
 ↓               ↓
Analytics    Main Agent
 Agent
```

---

## ✨ You're All Set!

Your IT Ticket AI System is now fully operational. The analytics agent will properly respond to trend analysis and reporting queries.

**Happy ticket analyzing! 🎉**

