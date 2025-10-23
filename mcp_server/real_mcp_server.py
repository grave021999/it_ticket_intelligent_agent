import json
import asyncio
import websockets
from typing import Dict, List, Any
from dataclasses import dataclass
import pandas as pd
import os
from openai import OpenAI

@dataclass
class MCPTool:
    name: str
    description: str
    inputSchema: Dict[str, Any]

@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mimeType: str

class MCPServer:
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.df = self._load_data()
        self._register_tools()
        self._register_resources()
    
    def _load_data(self):
        data_path = os.path.join(os.path.dirname(__file__), "../data/dummy_it_tickets.csv")
        try:
            df = pd.read_csv(data_path)
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def _register_tools(self):
        self.tools["search_tickets"] = MCPTool(
            name="search_tickets",
            description="Search and filter IT tickets based on various criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
        
        self.tools["list_tickets"] = MCPTool(
            name="list_tickets",
            description="List tickets with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of tickets to return"},
                    "offset": {"type": "integer", "description": "Number of tickets to skip"}
                },
                "required": ["limit", "offset"]
            }
        )
        
        self.tools["get_ticket_summary"] = MCPTool(
            name="get_ticket_summary",
            description="Get a summary of all tickets",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
        
        self.tools["analyze_ticket_trends"] = MCPTool(
            name="analyze_ticket_trends",
            description="Analyze trends in ticket data",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Analysis query"}
                },
                "required": ["query"]
            }
        )
    
    def _register_resources(self):
        self.resources["tickets_data"] = MCPResource(
            uri="file://tickets.csv",
            name="IT Tickets Data",
            description="Dataset of IT support tickets",
            mimeType="text/csv"
        )
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "IT Tickets MCP Server",
                "version": "1.0.0"
            }
        }
    
    async def handle_tools_list(self) -> Dict[str, Any]:
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        return {"tools": tools_list}
    
    async def handle_resources_list(self) -> Dict[str, Any]:
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mimeType
            })
        return {"resources": resources_list}
    
    async def handle_tools_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_tickets":
            return await self._search_tickets(arguments.get("query", ""))
        elif name == "list_tickets":
            return await self._list_tickets(
                arguments.get("limit", 10),
                arguments.get("offset", 0)
            )
        elif name == "get_ticket_summary":
            return await self._get_ticket_summary()
        elif name == "analyze_ticket_trends":
            return await self._analyze_ticket_trends(arguments.get("query", ""))
        else:
            return {"error": f"Unknown tool: {name}"}
    
    async def _search_tickets(self, query: str) -> Dict[str, Any]:
        if self.df.empty:
            return {"error": "No data available"}
        
        query_lower = query.lower()
        
        if "workload" in query_lower or "assigned to" in query_lower:
            return {"content": [{"type": "text", "text": self._analyze_workload()}]}
        
        if "summary" in query_lower or "overview" in query_lower or "statistics" in query_lower:
            return {"content": [{"type": "text", "text": self._get_comprehensive_summary()}]}
        
        filtered_df = self.df.copy()
        
        if "assigned to" in query_lower or "tickets for" in query_lower:
            name_parts = query_lower.split()
            for i, part in enumerate(name_parts):
                if part in ["to", "for"] and i + 1 < len(name_parts):
                    name = " ".join(name_parts[i+1:])
                    name = name.replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()
                    filtered_df = filtered_df[filtered_df['assigned_to'].str.contains(name, case=False, na=False)]
                    break
        
        if any(word in query_lower for word in ["network", "email", "software", "hardware", "access", "login", "vpn", "database", "server"]):
            for category in ["Network", "Email", "Software", "Hardware", "Access"]:
                if category.lower() in query_lower:
                    filtered_df = filtered_df[filtered_df['category'] == category]
                    break
        
        if "high priority" in query_lower or "critical" in query_lower:
            filtered_df = filtered_df[filtered_df['priority'].isin(['High', 'Critical'])]
        
        if "open" in query_lower:
            filtered_df = filtered_df[filtered_df['status'] == 'Open']
        
        if "closed" in query_lower:
            filtered_df = filtered_df[filtered_df['status'] == 'Closed']
        
        if len(filtered_df) == 0:
            return {"content": [{"type": "text", "text": f"No tickets found matching '{query}'"}]}
        
        result_text = f"Found {len(filtered_df)} tickets matching '{query}':\n\n"
        for idx, row in filtered_df.head(10).iterrows():
            result_text += f"{idx + 1}. {row['ticket_id']} - {row['category']} - {row['description']}\n"
            result_text += f"   Status: {row['status']}, Priority: {row['priority']}\n"
            result_text += f"   Assigned to: {row['assigned_to']}\n\n"
        
        if len(filtered_df) > 10:
            result_text += f"... and {len(filtered_df) - 10} more tickets\n"
        
        return {"content": [{"type": "text", "text": result_text}]}
    
    async def _list_tickets(self, limit: int, offset: int) -> Dict[str, Any]:
        if self.df.empty:
            return {"error": "No data available"}
        
        start_idx = offset
        end_idx = min(offset + limit, len(self.df))
        subset_df = self.df.iloc[start_idx:end_idx]
        
        result_text = f"Showing {len(subset_df)} tickets (offset: {offset}):\n\n"
        for idx, row in subset_df.iterrows():
            result_text += f"{idx - start_idx + 1}. {row['ticket_id']} - {row['category']} - {row['description']}\n"
            result_text += f"   Status: {row['status']}, Priority: {row['priority']}\n\n"
        
        return {"content": [{"type": "text", "text": result_text}]}
    
    async def _get_ticket_summary(self) -> Dict[str, Any]:
        if self.df.empty:
            return {"error": "No data available"}
        
        total_tickets = len(self.df)
        status_counts = self.df['status'].value_counts()
        priority_counts = self.df['priority'].value_counts()
        category_counts = self.df['category'].value_counts()
        
        summary_text = f"IT Tickets Summary ({total_tickets} total tickets)\n\n"
        summary_text += "Status Breakdown:\n"
        for status, count in status_counts.items():
            percentage = (count / total_tickets) * 100
            summary_text += f"- {status}: {count} ({percentage:.1f}%)\n"
        
        summary_text += "\nPriority Breakdown:\n"
        for priority, count in priority_counts.items():
            percentage = (count / total_tickets) * 100
            summary_text += f"- {priority}: {count} ({percentage:.1f}%)\n"
        
        summary_text += "\nCategory Breakdown:\n"
        for category, count in category_counts.items():
            percentage = (count / total_tickets) * 100
            summary_text += f"- {category}: {count} ({percentage:.1f}%)\n"
        
        return {"content": [{"type": "text", "text": summary_text}]}
    
    async def _analyze_ticket_trends(self, query: str) -> Dict[str, Any]:
        if self.df.empty:
            return {"error": "No data available"}
        
        query_lower = query.lower()
        
        target_category = None
        if "email" in query_lower:
            target_category = "Email"
        elif "network" in query_lower:
            target_category = "Network"
        elif "hardware" in query_lower:
            target_category = "Hardware"
        elif "software" in query_lower:
            target_category = "Software"
        elif "access" in query_lower:
            target_category = "Access"
        
        if target_category:
            category_tickets = self.df[self.df['category'] == target_category]
            trend_text = f"{target_category} Issues Analysis:\n\n"
            trend_text += f"Total {target_category} tickets: {len(category_tickets)}\n"
            
            if len(category_tickets) > 0:
                status_breakdown = category_tickets['status'].value_counts()
                trend_text += "\nStatus breakdown:\n"
                for status, count in status_breakdown.items():
                    percentage = (count / len(category_tickets)) * 100
                    trend_text += f"- {status}: {count} ({percentage:.1f}%)\n"
                
                priority_breakdown = category_tickets['priority'].value_counts()
                trend_text += "\nPriority breakdown:\n"
                for priority, count in priority_breakdown.items():
                    percentage = (count / len(category_tickets)) * 100
                    trend_text += f"- {priority}: {count} ({percentage:.1f}%)\n"
                
                trend_text += f"\nMost common {target_category.lower()} issues:\n"
                common_issues = category_tickets['description'].value_counts().head(5)
                for issue, count in common_issues.items():
                    trend_text += f"- {issue}: {count} occurrences\n"
                
                assignee_breakdown = category_tickets['assigned_to'].value_counts().head(5)
                trend_text += f"\nTop assignees for {target_category} issues:\n"
                for assignee, count in assignee_breakdown.items():
                    trend_text += f"- {assignee}: {count} tickets\n"
            else:
                trend_text += f"No {target_category} tickets found in the dataset.\n"
            
            return {"content": [{"type": "text", "text": trend_text}]}
        else:
            total_tickets = len(self.df)
            trend_text = f"Overall Ticket Trends Analysis:\n\n"
            trend_text += f"Total tickets analyzed: {total_tickets}\n\n"
            
            category_counts = self.df['category'].value_counts()
            trend_text += "Category Distribution:\n"
            for category, count in category_counts.items():
                percentage = (count / total_tickets) * 100
                trend_text += f"- {category}: {count} ({percentage:.1f}%)\n"
            
            status_counts = self.df['status'].value_counts()
            trend_text += "\nStatus Distribution:\n"
            for status, count in status_counts.items():
                percentage = (count / total_tickets) * 100
                trend_text += f"- {status}: {count} ({percentage:.1f}%)\n"
            
            priority_counts = self.df['priority'].value_counts()
            trend_text += "\nPriority Distribution:\n"
            for priority, count in priority_counts.items():
                percentage = (count / total_tickets) * 100
                trend_text += f"- {priority}: {count} ({percentage:.1f}%)\n"
            
            assignee_counts = self.df['assigned_to'].value_counts().head(5)
            trend_text += "\nTop 5 Assignees:\n"
            for assignee, count in assignee_counts.items():
                trend_text += f"- {assignee}: {count} tickets\n"
            
            return {"content": [{"type": "text", "text": trend_text}]}
    
    def _analyze_workload(self) -> str:
        workload = self.df['assigned_to'].value_counts()
        top_assignees = workload.head(10)
        result_text = "Workload Analysis - Top 10 Assignees:\n\n"
        for i, (assignee, count) in enumerate(top_assignees.items(), 1):
            assignee_tickets = self.df[self.df['assigned_to'] == assignee]
            open_count = len(assignee_tickets[assignee_tickets['status'] == 'Open'])
            high_priority = len(assignee_tickets[assignee_tickets['priority'].isin(['High', 'Critical'])])
            result_text += f"{i}. {assignee}: {count} total tickets\n"
            result_text += f"   - Open tickets: {open_count}\n"
            result_text += f"   - High/Critical priority: {high_priority}\n\n"
        total_tickets = len(self.df)
        unique_assignees = len(workload)
        avg_workload = total_tickets / unique_assignees
        result_text += f"Overall Statistics:\n"
        result_text += f"- Total tickets: {total_tickets}\n"
        result_text += f"- Unique assignees: {unique_assignees}\n"
        result_text += f"- Average workload: {avg_workload:.1f} tickets per person\n"
        return result_text
    
    def _get_comprehensive_summary(self) -> str:
        total_tickets = len(self.df)
        status_counts = self.df['status'].value_counts()
        status_text = "Status Breakdown:\n"
        for status, count in status_counts.items():
            percentage = (count / total_tickets) * 100
            status_text += f"- {status}: {count} ({percentage:.1f}%)\n"
        priority_counts = self.df['priority'].value_counts()
        priority_text = "\nPriority Breakdown:\n"
        for priority, count in priority_counts.items():
            percentage = (count / total_tickets) * 100
            priority_text += f"- {priority}: {count} ({percentage:.1f}%)\n"
        category_counts = self.df['category'].value_counts()
        category_text = "\nCategory Breakdown:\n"
        for category, count in category_counts.items():
            percentage = (count / total_tickets) * 100
            category_text += f"- {category}: {count} ({percentage:.1f}%)\n"
        assignee_counts = self.df['assigned_to'].value_counts().head(5)
        assignee_text = "\nTop 5 Assignees:\n"
        for assignee, count in assignee_counts.items():
            assignee_text += f"- {assignee}: {count} tickets\n"
        summary = f"IT Tickets Summary ({total_tickets} total tickets)\n\n"
        summary += status_text + priority_text + category_text + assignee_text
        return summary
    
    async def handle_message(self, message: str) -> str:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return json.dumps({"error": {"code": -32700, "message": "Parse error"}})
        
        if "method" not in data:
            return json.dumps({"error": {"code": -32600, "message": "Invalid Request"}})
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_tools_list()
            elif method == "resources/list":
                result = await self.handle_resources_list()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.handle_tools_call(tool_name, arguments)
            else:
                return json.dumps({"error": {"code": -32601, "message": "Method not found"}})
            
            return json.dumps({"result": result, "id": request_id})
            
        except Exception as e:
            return json.dumps({"error": {"code": -32603, "message": str(e)}, "id": request_id})

mcp_server = MCPServer()

async def handle_client(websocket):
    try:
        async for message in websocket:
            response = await mcp_server.handle_message(message)
            await websocket.send(response)
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"Error handling client: {e}")

async def start_mcp_server():
    print("Starting MCP Server on ws://localhost:8080")
    try:
        async with websockets.serve(
            handle_client, 
            "localhost", 
            8080,
            ping_interval=30,
            ping_timeout=20,
            close_timeout=10
        ):
            print("MCP Server is running and ready for connections")
            await asyncio.Future()
    except Exception as e:
        print(f"MCP Server error: {e}")
        print("Restarting MCP Server in 5 seconds...")
        await asyncio.sleep(5)
        await start_mcp_server()

if __name__ == "__main__":
    try:
        asyncio.run(start_mcp_server())
    except KeyboardInterrupt:
        print("MCP Server stopped by user")
    except Exception as e:
        print(f"MCP Server failed to start: {e}")
        print("Please check if port 8080 is available")