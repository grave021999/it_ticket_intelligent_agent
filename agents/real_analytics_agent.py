import asyncio
import websockets
import json
import time
import logging
import os
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulletproofAnalyticsAgent:
    def __init__(self):
        self.agent_id = "analytics_agent"
        self.name = "Analytics Agent"
        self.a2a_server = "ws://localhost:9090"
        self.mcp_server = "ws://localhost:8080"
        self.websocket = None
        self.mcp_websocket = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def create_connection(self):
        try:
            logger.info(f"Creating connection to {self.a2a_server}")
            
            self.websocket = await websockets.connect(
                self.a2a_server,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=2**20,
                open_timeout=10,
                compression=None,
                subprotocols=None
            )
            
            logger.info("WebSocket connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
                self.websocket = None
            return False

    async def connect_to_mcp(self):
        try:
            logger.info(f"Connecting to MCP server at {self.mcp_server}")
            self.mcp_websocket = await websockets.connect(
                self.mcp_server,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=2**20,
                open_timeout=10
            )
            logger.info("MCP server connection established")
            
            test_message = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "analytics_agent", "version": "1.0.0"}
                }
            }
            
            await self.mcp_websocket.send(json.dumps(test_message))
            response = await asyncio.wait_for(self.mcp_websocket.recv(), timeout=5.0)
            logger.info("MCP server connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            if self.mcp_websocket:
                try:
                    await self.mcp_websocket.close()
                except:
                    pass
                self.mcp_websocket = None
            return False

    async def register_with_a2a(self):
        try:
            if not self.websocket:
                return False
                
            register_message = {
                "type": "agent_register",
                "agent_id": self.agent_id,
                "name": self.name,
                "capabilities": [
                    "statistical_analysis",
                    "reporting",
                    "trend_analysis",
                    "data_summarization"
                ],
                "endpoint": "ws://localhost:9090",
                "metadata": {
                    "version": "1.0.0",
                    "description": "Performs ticket analytics and trend reporting"
                }
            }
            
            await self.websocket.send(json.dumps(register_message))
            logger.info(f"Registration message sent for {self.name}")
            
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            result = json.loads(response)
            
            if result.get("status") == "success":
                logger.info(f"Successfully registered {self.name}")
                self.reconnect_attempts = 0
                return True
            else:
                logger.error(f"Registration failed: {result.get('message')}")
                return False
                
        except asyncio.TimeoutError:
            logger.error("Registration timeout")
            return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False

    async def handle_message(self, message):
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "delegate_task":
                await self.handle_task_delegation(data)
            elif message_type == "task_assignment":
                await self.handle_task_delegation(data)
            elif message_type == "discover_agents":
                await self.handle_discovery_request()
            elif message_type == "ping":
                await self.handle_ping()
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_task_delegation(self, data):
        try:
            task_id = data.get("task_id")
            from_agent = data.get("from_agent")
            task_type = data.get("task_type")
            payload = data.get("payload", {})
            query = payload.get("query", "")
            
            logger.info(f"Processing task {task_id} from {from_agent}: {task_type}")
            logger.info(f"Query: {query}")
            
            result = await self.process_analytics_task(query)
            
            completion_message = {
                "type": "task_completed",
                "task_id": task_id,
                "from_agent": self.agent_id,
                "to_agent": from_agent,
                "result": result
            }
            
            await self.websocket.send(json.dumps(completion_message))
            logger.info(f"Task {task_id} completed and response sent")
            
        except Exception as e:
            logger.error(f"Error handling task delegation: {e}")
            
            try:
                failure_message = {
                    "type": "task_failed",
                    "task_id": data.get("task_id"),
                    "from_agent": self.agent_id,
                    "to_agent": data.get("from_agent"),
                    "error": str(e)
                }
                await self.websocket.send(json.dumps(failure_message))
            except:
                pass

    async def process_analytics_task(self, query):
        try:
            if not self.mcp_websocket:
                logger.error("MCP server not connected, attempting to reconnect...")
                if not await self.connect_to_mcp():
                    logger.error("Failed to reconnect to MCP server")
                    return {"error": "MCP server not connected and reconnection failed"}
            
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "analytics_agent",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self.mcp_websocket.send(json.dumps(init_message))
            init_response = await asyncio.wait_for(self.mcp_websocket.recv(), timeout=10.0)
            logger.info("MCP server initialized")
            
            tools_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            await self.mcp_websocket.send(json.dumps(tools_message))
            tools_response = await asyncio.wait_for(self.mcp_websocket.recv(), timeout=10.0)
            tools_data = json.loads(tools_response)
            logger.info(f"Available tools: {[tool['name'] for tool in tools_data.get('result', {}).get('tools', [])]}")
            
            tool_to_use = self._determine_tool_for_query(query)
            logger.info(f"Using tool: {tool_to_use}")
            
            if tool_to_use == "analyze_ticket_trends":
                tool_message = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "analyze_ticket_trends",
                        "arguments": {"query": query}
                    }
                }
            elif tool_to_use == "get_ticket_summary":
                tool_message = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "get_ticket_summary",
                        "arguments": {}
                    }
                }
            else:
                tool_message = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "search_tickets",
                        "arguments": {"query": query}
                    }
                }
            
            await self.mcp_websocket.send(json.dumps(tool_message))
            tool_response = await asyncio.wait_for(self.mcp_websocket.recv(), timeout=30.0)
            tool_data = json.loads(tool_response)
            
            if "error" in tool_data:
                logger.error(f"MCP tool error: {tool_data['error']}")
                return {"error": f"MCP tool error: {tool_data['error']}"}
            
            result_content = tool_data.get("result", {}).get("content", [])
            if result_content and len(result_content) > 0:
                analysis_text = result_content[0].get("text", "No analysis available")
            else:
                analysis_text = "No analysis available"
            
            enhanced_analysis = await self._enhance_analysis_with_ai(query, analysis_text)
            
            result = {
                "summary": f"Analytics completed for: '{query}'",
                "details": {
                    "raw_analysis": analysis_text,
                    "enhanced_analysis": enhanced_analysis,
                    "tool_used": tool_to_use,
                    "timestamp": time.time()
                }
            }
            
            return result
            
        except asyncio.TimeoutError:
            logger.error("MCP server timeout")
            return {"error": "MCP server timeout"}
        except Exception as e:
            logger.error(f"Analytics processing failed: {e}")
            return {"error": f"Analytics processing failed: {str(e)}"}

    def _determine_tool_for_query(self, query):
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["trend", "pattern", "analysis", "trends"]):
            return "analyze_ticket_trends"
        elif any(word in query_lower for word in ["summary", "overview", "statistics", "total"]):
            return "get_ticket_summary"
        else:
            return "search_tickets"

    async def _enhance_analysis_with_ai(self, query, raw_analysis):
        try:
            if not self.client:
                return raw_analysis
            
            prompt = f"""
            Based on the following IT ticket analysis data, provide insights and recommendations:
            
            Query: {query}
            Raw Analysis: {raw_analysis}
            
            Please provide:
            1. Key insights from the data
            2. Trends and patterns identified
            3. Actionable recommendations
            4. Priority areas for improvement
            
            Format your response as a structured analysis.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}")
            return raw_analysis

    async def handle_discovery_request(self):
        try:
            response = {
                "type": "discovery_response",
                "agent_id": self.agent_id,
                "name": self.name,
                "capabilities": [
                    "statistical_analysis",
                    "reporting",
                    "trend_analysis",
                    "data_summarization"
                ],
                "status": "online"
            }
            await self.websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"Error handling discovery: {e}")

    async def handle_ping(self):
        try:
            pong = {"type": "pong", "timestamp": time.time()}
            await self.websocket.send(json.dumps(pong))
        except Exception as e:
            logger.error(f"Error handling ping: {e}")

    async def message_loop(self):
        logger.info("Starting message loop...")
        self.running = True
        
        try:
            while self.running and self.websocket:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    await self.handle_message(message)
                    
                except asyncio.TimeoutError:
                    continue
                except (websockets.ConnectionClosed, websockets.InvalidMessage, EOFError) as e:
                    logger.warning(f"Connection error: {e}")
                    break
                except websockets.exceptions.InvalidMessage as e:
                    logger.warning(f"Invalid message error: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error in message loop: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in message loop: {e}")
        finally:
            self.running = False
            logger.info("Message loop stopped")

    async def run(self):
        logger.info("Starting Bulletproof Analytics Agent...")
        
        while True:
            try:
                if await self.create_connection():
                    if await self.connect_to_mcp():
                        if await self.register_with_a2a():
                            await self.message_loop()
                        else:
                            logger.error("Failed to register with A2A server")
                            await self.cleanup_connection()
                    else:
                        logger.error("Failed to connect to MCP server")
                        await self.cleanup_connection()
                else:
                    logger.error("Failed to create A2A connection")
                
                await self.cleanup_connection()
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts} in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    logger.error("Max reconnection attempts reached. Stopping agent.")
                    break
                    
            except KeyboardInterrupt:
                logger.info("Stopping Analytics Agent...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                await self.cleanup_connection()
                await asyncio.sleep(self.reconnect_delay)

    async def cleanup_connection(self):
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
        
        if self.mcp_websocket:
            try:
                await self.mcp_websocket.close()
            except:
                pass
            self.mcp_websocket = None

async def main():
    agent = BulletproofAnalyticsAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())