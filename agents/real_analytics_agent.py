import asyncio
import websockets
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulletproofAnalyticsAgent:
    def __init__(self):
        self.agent_id = "analytics_agent"
        self.name = "Analytics Agent"
        self.a2a_server = "ws://localhost:9090"
        self.websocket = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5

    async def create_connection(self):
        """Create a robust WebSocket connection with proper error handling"""
        try:
            logger.info(f"Creating connection to {self.a2a_server}")
            
            # Create connection with robust parameters
            self.websocket = await websockets.connect(
                self.a2a_server,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5,
                max_size=2**20,
                open_timeout=10,
                compression=None,  # Disable compression to avoid issues
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

    async def register_with_a2a(self):
        """Register the agent with A2A server"""
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
            
            # Wait for registration response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            result = json.loads(response)
            
            if result.get("status") == "success":
                logger.info(f"Successfully registered {self.name}")
                self.reconnect_attempts = 0  # Reset on successful registration
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
        """Handle incoming messages from A2A server"""
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
        """Handle delegated tasks"""
        try:
            task_id = data.get("task_id")
            from_agent = data.get("from_agent")
            task_type = data.get("task_type")
            payload = data.get("payload", {})
            query = payload.get("query", "")
            
            logger.info(f"Processing task {task_id} from {from_agent}: {task_type}")
            logger.info(f"Query: {query}")
            
            # Process the analytics task
            result = await self.process_analytics_task(query)
            
            # Send completion response
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
            
            # Send failure response
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
        """Process analytics tasks and return results"""
        try:
            # Simulate analytics processing
            await asyncio.sleep(1)
            
            result = {
                "summary": f"Analytics completed for: '{query}'",
                "details": {
                    "tickets_analyzed": 150,
                    "trend_analysis": "Network issues showing 15% increase",
                    "top_categories": ["Network", "Email", "Hardware"],
                    "priority_distribution": {
                        "High": 25,
                        "Medium": 60,
                        "Low": 15
                    },
                    "recommendations": [
                        "Focus on network infrastructure improvements",
                        "Consider additional email support resources",
                        "Monitor hardware failure patterns"
                    ]
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Analytics processing failed: {str(e)}"
            }

    async def handle_discovery_request(self):
        """Handle discovery requests"""
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
        """Handle ping messages"""
        try:
            pong = {"type": "pong", "timestamp": time.time()}
            await self.websocket.send(json.dumps(pong))
        except Exception as e:
            logger.error(f"Error handling ping: {e}")

    async def message_loop(self):
        """Main message processing loop"""
        logger.info("Starting message loop...")
        self.running = True
        
        try:
            while self.running and self.websocket:
                try:
                    # Wait for messages with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    await self.handle_message(message)
                    
                except asyncio.TimeoutError:
                    # No message received, continue
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
        """Main run loop with robust reconnection"""
        logger.info("Starting Bulletproof Analytics Agent...")
        
        while True:
            try:
                # Create connection
                if await self.create_connection():
                    # Register with A2A
                    if await self.register_with_a2a():
                        # Start message loop
                        await self.message_loop()
                    else:
                        logger.error("Failed to register with A2A server")
                        await self.cleanup_connection()
                else:
                    logger.error("Failed to create connection")
                
                # If we reach here, connection was lost
                await self.cleanup_connection()
                
                # Reconnection logic
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
        """Clean up WebSocket connection"""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None

async def main():
    agent = BulletproofAnalyticsAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())