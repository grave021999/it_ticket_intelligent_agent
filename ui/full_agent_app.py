import streamlit as st
import asyncio
import json
import websockets
from typing import Dict, Any
import time
import os
from openai import OpenAI

st.set_page_config(
    page_title="IT Ticket AI System",
    page_icon="📋",
    layout="wide"
)

class AgentUIManager:
    def __init__(self):
        self.a2a_websocket = None
        self.mcp_websocket = None
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def cleanup_connections(self):
        try:
            if self.a2a_websocket:
                await self.a2a_websocket.close()
                self.a2a_websocket = None
        except:
            pass
        
        try:
            if self.mcp_websocket:
                await self.mcp_websocket.close()
                self.mcp_websocket = None
        except:
            pass
        
    async def connect_to_a2a(self):
        try:
            if self.a2a_websocket:
                try:
                    await self.a2a_websocket.close()
                except:
                    pass
                self.a2a_websocket = None
            
            self.a2a_websocket = await websockets.connect(
                "ws://localhost:9090",
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=2**20,
                open_timeout=5
            )
            return True
        except Exception as e:
            st.error(f"Failed to connect to A2A server: {e}")
            self.a2a_websocket = None
            return False
    
    async def connect_to_mcp(self):
        try:
            if self.mcp_websocket:
                try:
                    await self.mcp_websocket.close()
                except:
                    pass
                self.mcp_websocket = None
            
            self.mcp_websocket = await websockets.connect(
                "ws://localhost:8080",
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=2**20,
                open_timeout=5
            )
            init_message = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "Agent UI Manager",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            }
            await self.mcp_websocket.send(json.dumps(init_message))
            response = await self.mcp_websocket.recv()
            return True
        except Exception as e:
            st.error(f"Failed to connect to MCP server: {e}")
            self.mcp_websocket = None
            return False
    
    async def discover_agents(self):
        if not self.a2a_websocket:
            if not await self.connect_to_a2a():
                return []
        
        try:
            discovery_message = {
                "type": "discover_agents"
            }
            await self.a2a_websocket.send(json.dumps(discovery_message))
            response = await self.a2a_websocket.recv()
            result = json.loads(response)
            
            if result.get("status") == "success":
                return result.get("agents", [])
            else:
                return []
        except Exception as e:
            st.error(f"Error discovering agents: {e}")
            return []
    
    async def delegate_to_analytics_agent(self, query: str) -> Dict[str, Any]:
        if not self.a2a_websocket:
            if not await self.connect_to_a2a():
                return {"error": "Could not connect to A2A server"}
        
        try:
            agents = await self.discover_agents()
            analytics_agent = None
            
            for agent in agents:
                if agent.get("agent_id") == "analytics_agent":
                    analytics_agent = agent
                    break
            
            if not analytics_agent:
                st.warning("Analytics Agent not available, using MCP trend analysis...")
                return await self._fallback_trend_analysis(query)
            
            task_message = {
                "type": "delegate_task",
                "from_agent": "ui_manager",
                "to_agent": "analytics_agent",
                "task_type": "analyze_trends",
                "payload": {
                    "query": query
                }
            }
            
            await self.a2a_websocket.send(json.dumps(task_message))
            
            try:
                response = await asyncio.wait_for(self.a2a_websocket.recv(), timeout=3.0)
                result = json.loads(response)
                
                if result.get("status") == "success":
                    task_id = result.get("task_id")
                    completion_result = await self._wait_for_task_completion(task_id)
                    
                    if "error" in completion_result:
                        st.warning(f"Analytics Agent task failed: {completion_result['error']}. Using fallback...")
                        return await self._fallback_trend_analysis(query)
                    
                    return completion_result
                else:
                    st.warning(f"Task delegation failed: {result.get('message')}. Using fallback...")
                    return await self._fallback_trend_analysis(query)
            except asyncio.TimeoutError:
                st.warning("Analytics Agent response timeout. Using fallback...")
                return await self._fallback_trend_analysis(query)
                
        except Exception as e:
            st.warning(f"Analytics Agent error: {e}. Using fallback...")
            return await self._fallback_trend_analysis(query)
    
    async def _fallback_trend_analysis(self, query: str) -> Dict[str, Any]:
        try:
            result = await self.execute_mcp_tool("analyze_ticket_trends", {"query": query})
            if "error" not in result:
                return {
                    "status": "success",
                    "approach": "mcp_trend_analysis",
                    "result": result,
                    "query": query
                }
            else:
                search_result = await self.execute_mcp_tool("search_tickets", {"query": query})
                if "error" not in search_result:
                    return {
                        "status": "success",
                        "approach": "mcp_search",
                        "result": search_result,
                        "query": query
                    }
                else:
                    return await self._ai_direct_response(query)
        except Exception as e:
            return await self._ai_direct_response(query)
    
    async def _wait_for_task_completion(self, task_id: str) -> Dict[str, Any]:
        try:
            
            timeout = 15
            poll_interval = 0.5
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    status_message = {
                        "type": "task_status",
                        "task_id": task_id
                    }
                    await self.a2a_websocket.send(json.dumps(status_message))
                    
                    response = await asyncio.wait_for(self.a2a_websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    
                    if data.get("status") == "success" and "task" in data:
                        task = data["task"]
                        task_status = task.get("status")
                        
                        if task_status == "completed":
                            return {
                                "status": "success",
                                "result": task.get("result", {}),
                                "approach": "analytics_agent"
                            }
                        elif task_status == "failed":
                            return {"error": "Task execution failed"}
                    
                    await asyncio.sleep(poll_interval)
                        
                except asyncio.TimeoutError:
                    continue
                except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidMessage, EOFError):
                    return {"error": "Connection lost while waiting for task completion"}
                    
            return {"error": f"Task {task_id} timed out after {timeout} seconds"}
                    
        except Exception as e:
            return {"error": f"Error waiting for task completion: {e}"}
    
    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self.mcp_websocket:
            if not await self.connect_to_mcp():
                return {"error": "Not connected to MCP server"}
        
        try:
            tool_call = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 2
            }
            await self.mcp_websocket.send(json.dumps(tool_call))
            response = await self.mcp_websocket.recv()
            result = json.loads(response)
            
            if "result" in result:
                return result["result"]
            else:
                return {"error": result.get("error", "Unknown error")}
                
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    async def process_user_query(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["trend", "analysis", "analyze", "pattern", "insight", "report"]):
            result = await self.delegate_to_analytics_agent(query)
            if "error" not in result:
                return result
        
        if any(word in query_lower for word in ["summary", "overview", "statistics", "total"]):
            result = await self.execute_mcp_tool("get_ticket_summary", {})
            if "error" not in result:
                return {
                    "status": "success",
                    "approach": "summary",
                    "result": result,
                    "query": query
                }
        
        if any(word in query_lower for word in ["search", "find", "show", "list", "tickets"]):
            result = await self.execute_mcp_tool("search_tickets", {"query": query})
            if "error" not in result:
                return {
                    "status": "success",
                    "approach": "search",
                    "result": result,
                    "query": query
                }
        
        return await self._ai_direct_response(query)
    
    async def _ai_direct_response(self, query: str) -> Dict[str, Any]:
        try:
            summary_result = await self.execute_mcp_tool("get_ticket_summary", {})
            context_data = ""
            if "error" not in summary_result and "content" in summary_result:
                context_data = summary_result["content"][0].get("text", "")
            
            ai_prompt = f"""
            You are an expert IT support analyst. Answer this user query about IT tickets in natural, conversational language:
            
            User Query: "{query}"
            
            System Context (if available):
            {context_data}
            
            Provide a helpful, professional response in natural human language. Be conversational and friendly.
            If you need specific data that isn't available, explain what information would be needed and suggest how to get it.
            
            Format your response as a natural conversation, not as technical data.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a friendly IT support analyst. Provide helpful, conversational responses about IT ticket management in natural human language. Be warm, professional, and easy to understand."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "approach": "ai_direct",
                "ai_response": ai_response,
                "query": query
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI response failed: {str(e)}",
                "query": query
            }
    
    async def _convert_analytics_to_natural_language(self, analytics_result: Dict[str, Any], query: str) -> str:
        try:
            summary = analytics_result.get("summary", "")
            details = analytics_result.get("details", {})
            
            raw_analysis = details.get("raw_analysis", "")
            enhanced_analysis = details.get("enhanced_analysis", "")
            tool_used = details.get("tool_used", "unknown")
            
            context = f"""
            Summary: {summary}
            Tool Used: {tool_used}
            
            Raw Analysis Data:
            {raw_analysis}
            
            AI-Enhanced Analysis:
            {enhanced_analysis}
            """
            
            conversion_prompt = f"""
            You are a friendly IT support analyst explaining analytics results to a colleague.
            
            Original Query: "{query}"
            
            Analytics Data:
            {context}
            
            Please provide a clear, conversational explanation of these analytics results. 
            Structure your response naturally:
            1. Start with a brief overview of what was found
            2. Explain the key trends and patterns from the data
            3. Highlight the important statistics and numbers
            4. Share the actionable recommendations and insights
            
            Use natural language, be friendly and professional, and make it easy to understand.
            Focus on the real data and insights provided, not generic responses.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a friendly IT support analyst who excels at explaining data insights in clear, conversational language. You help people understand trends and make data-driven decisions."},
                    {"role": "user", "content": conversion_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
                
        except Exception as e:
            summary = analytics_result.get("summary", "")
            details = analytics_result.get("details", {})
            
            fallback = f"{summary}\n\n"
            fallback += f"I analyzed {details.get('tickets_analyzed', 0)} tickets and found some interesting patterns:\n\n"
            fallback += f"**Trends:** {details.get('trend_analysis', 'No specific trends identified')}\n\n"
            
            if details.get('top_categories'):
                fallback += f"**Top Categories:** {', '.join(details.get('top_categories', []))}\n\n"
            
            if details.get('recommendations'):
                fallback += "**Recommendations:**\n"
                for rec in details.get('recommendations', []):
                    fallback += f"- {rec}\n"
            
            return fallback
    
    async def _convert_to_natural_language(self, result: Dict[str, Any], query: str) -> str:
        try:
            if "content" in result:
                content = result.get("content", [{}])[0]
                text = content.get("text", "No response text")
                
                conversion_prompt = f"""
                Convert this technical IT ticket system response into natural, conversational language:
                
                Original Query: "{query}"
                Technical Response: "{text}"
                
                Make it sound like a friendly IT support analyst explaining the results to a colleague.
                Be conversational, helpful, and easy to understand.
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a friendly IT support analyst. Convert technical data into natural, conversational explanations."},
                        {"role": "user", "content": conversion_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=600
                )
                
                return response.choices[0].message.content.strip()
            else:
                return "I found some information, but I need to process it better to give you a clear answer."
                
        except Exception as e:
            return f"I found some data, but I'm having trouble converting it to a clear explanation. Here's what I found: {str(e)}"
    
    async def check_system_status(self) -> Dict[str, Any]:
        status = {
            "mcp_server": False,
            "a2a_server": False,
            "analytics_agent": False
        }
        
        try:
            async with websockets.connect("ws://localhost:8080") as ws:
                status["mcp_server"] = True
        except:
            pass
        
        try:
            async with websockets.connect("ws://localhost:9090") as ws:
                status["a2a_server"] = True
        except:
            pass
        
        try:
            if self.a2a_websocket:
                agents = await self.discover_agents()
                for agent in agents:
                    if agent.get("agent_id") == "analytics_agent":
                        status["analytics_agent"] = True
                        break
        except:
            pass
        
        return status

def main():
    st.title("🤖 AI Ticket Assistant")
    st.markdown("Ask me anything about your IT tickets")
    
    ui_manager = AgentUIManager()
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    query = st.text_input(
        "What would you like to know about your tickets?",
        placeholder="e.g., 'Show me network issues' or 'Analyze trends in high priority tickets'",
        key="query_input"
    )
    
    if st.button("Ask AI", type="primary"):
        if query:
            with st.spinner("Thinking..."):
                loop = None
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(ui_manager.process_user_query(query))
                    
                    st.session_state.query_history.append({
                        "query": query,
                        "result": result,
                        "timestamp": time.time()
                    })
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        if result.get("status") == "success":
                            approach = result.get("approach", "unknown")
                            
                            if approach == "ai_direct":
                                ai_response = result.get("ai_response", "No AI response")
                                st.write(ai_response)
                            elif approach == "analytics_agent":
                                analytics_result = result.get("result", {})
                                
                                natural_response = loop.run_until_complete(
                                    ui_manager._convert_analytics_to_natural_language(analytics_result, query)
                                )
                                st.write(natural_response)
                            elif approach in ["summary", "search", "mcp_trend_analysis", "mcp_search"]:
                                mcp_result = result.get("result", {})
                                
                                natural_response = loop.run_until_complete(ui_manager._convert_to_natural_language(mcp_result, query))
                                st.write(natural_response)
                            else:
                                st.json(result)
                        else:
                            st.error(f"Error: {result.get('message', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error processing query: {e}")
                finally:
                    try:
                        if loop:
                            loop.run_until_complete(ui_manager.cleanup_connections())
                            loop.close()
                    except:
                        pass
        else:
            st.warning("Please enter a question")
    
    if st.session_state.query_history:
        st.markdown("---")
        st.subheader("Recent Questions")
        for i, entry in enumerate(reversed(st.session_state.query_history[-3:])):
            with st.expander(f"Q: {entry['query'][:60]}..."):
                st.write(f"**Question:** {entry['query']}")
                if "error" in entry['result']:
                    st.error(f"**Error:** {entry['result']['error']}")
                else:
                    if entry['result'].get('approach') == 'analytics_agent':
                        analytics_result = entry['result'].get('result', {})
                        if "summary" in analytics_result:
                            st.write(f"**Response:** {analytics_result['summary']}")
                    elif entry['result'].get('approach') == 'ai_direct':
                        st.write(f"**Response:** {entry['result'].get('ai_response', 'No response')}")
                    else:
                        st.write("**Response:** [AI processed successfully]")

if __name__ == "__main__":
    main()