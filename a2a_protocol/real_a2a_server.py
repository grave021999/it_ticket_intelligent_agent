#!/usr/bin/env python3
import asyncio
import json
import websockets
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class A2AAgent:
    agent_id: str
    name: str
    capabilities: List[str]
    status: str
    endpoint: str
    last_seen: datetime
    metadata: Dict[str, Any]

@dataclass
class A2ATask:
    task_id: str
    from_agent: str
    to_agent: str
    task_type: str
    payload: Dict[str, Any]
    status: str
    created_at: datetime
    completed_at: datetime = None
    result: Dict[str, Any] = None

class A2AServer:
    def __init__(self):
        self.agents: Dict[str, A2AAgent] = {}
        self.tasks: Dict[str, A2ATask] = {}
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
    
    async def register_agent(self, agent_data: Dict[str, Any], websocket) -> Dict[str, Any]:
        agent_id = agent_data.get("agent_id", str(uuid.uuid4()))
        agent = A2AAgent(
            agent_id=agent_id,
            name=agent_data.get("name", f"Agent-{agent_id[:8]}"),
            capabilities=agent_data.get("capabilities", []),
            status="available",
            endpoint=agent_data.get("endpoint", ""),
            last_seen=datetime.now(),
            metadata=agent_data.get("metadata", {})
        )
        self.agents[agent_id] = agent
        self.connections[agent_id] = websocket
        print(f"Agent registered: {agent.name} ({agent_id})")
        return {
            "status": "success",
            "agent_id": agent_id,
            "message": f"Agent {agent.name} registered successfully"
        }
    
    async def discover_agents(self, capability_filter: str = None) -> Dict[str, Any]:
        available_agents = []
        for agent in self.agents.values():
            if agent.status == "available":
                if capability_filter is None or capability_filter in agent.capabilities:
                    available_agents.append({
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "capabilities": agent.capabilities,
                        "endpoint": agent.endpoint,
                        "last_seen": agent.last_seen.isoformat()
                    })
        return {
            "status": "success",
            "agents": available_agents,
            "count": len(available_agents)
        }
    
    async def delegate_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        from_agent = task_data.get("from_agent")
        to_agent = task_data.get("to_agent")
        task_type = task_data.get("task_type", "general")
        payload = task_data.get("payload", {})
        
        if to_agent not in self.agents:
            return {
                "status": "error",
                "message": f"Target agent {to_agent} not found"
            }
        
        if self.agents[to_agent].status != "available":
            return {
                "status": "error", 
                "message": f"Target agent {to_agent} is not available"
            }
        
        task = A2ATask(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            task_type=task_type,
            payload=payload,
            status="pending",
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        
        if to_agent in self.connections:
            task_message = {
                "type": "task_assignment",
                "task_id": task_id,
                "from_agent": from_agent,
                "task_type": task_type,
                "payload": payload
            }
            
            try:
                await self.connections[to_agent].send(json.dumps(task_message))
                task.status = "in_progress"
                return {
                    "status": "success",
                    "task_id": task_id,
                    "message": f"Task delegated to {to_agent}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to send task: {str(e)}"
                }
        else:
            return {
                "status": "error",
                "message": f"Agent {to_agent} is not connected"
            }
    
    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {
                "status": "error",
                "message": f"Task {task_id} not found"
            }
        
        task = self.tasks[task_id]
        task.status = "completed"
        task.completed_at = datetime.now()
        task.result = result
        
        if task.from_agent in self.connections:
            completion_message = {
                "type": "task_completed",
                "task_id": task_id,
                "result": result
            }
            
            try:
                await self.connections[task.from_agent].send(json.dumps(completion_message))
            except Exception as e:
                print(f"Failed to notify task completion: {e}")
        
        return {
            "status": "success",
            "message": f"Task {task_id} completed successfully"
        }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        if task_id not in self.tasks:
            return {
                "status": "error",
                "message": f"Task {task_id} not found"
            }
        
        task = self.tasks[task_id]
        return {
            "status": "success",
            "task": {
                "task_id": task.task_id,
                "from_agent": task.from_agent,
                "to_agent": task.to_agent,
                "task_type": task.task_type,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "result": task.result
            }
        }
    
    async def handle_message(self, message: str, websocket) -> str:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return json.dumps({
                "status": "error",
                "message": "Invalid JSON format"
            })
        
        message_type = data.get("type")
        
        if message_type == "agent_register":
            result = await self.register_agent(data, websocket)
            return json.dumps(result)
        
        elif message_type == "discover_agents":
            result = await self.discover_agents(data.get("capability_filter"))
            return json.dumps(result)
        
        elif message_type == "delegate_task":
            result = await self.delegate_task(data)
            return json.dumps(result)
        
        elif message_type == "task_completed":
            result = await self.complete_task(data.get("task_id"), data.get("result", {}))
            return json.dumps(result)
        
        elif message_type == "task_status":
            result = await self.get_task_status(data.get("task_id"))
            return json.dumps(result)
        
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unknown message type: {message_type}"
            })

a2a_server = A2AServer()

async def handle_a2a_client(websocket):
    print(f"A2A client connected: {websocket.remote_address}")
    client_agent_id = None
    
    try:
        async for message in websocket:
            try:
                print(f"A2A message: {message}")
                response = await a2a_server.handle_message(message, websocket)
                print(f"A2A response: {response}")
                await websocket.send(response)
                
                data = json.loads(message)
                if data.get("type") == "agent_register":
                    client_agent_id = data.get("agent_id")
                    print(f"Registered agent: {client_agent_id}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                error_response = json.dumps({
                    "status": "error",
                    "message": f"Invalid JSON: {str(e)}"
                })
                try:
                    await websocket.send(error_response)
                except:
                    pass
            except (websockets.ConnectionClosed, websockets.InvalidMessage, EOFError) as e:
                print(f"Connection error: {e}")
                break
            except Exception as e:
                print(f"Error processing message: {e}")
                try:
                    error_response = json.dumps({
                        "status": "error",
                        "message": f"Processing error: {str(e)}"
                    })
                    await websocket.send(error_response)
                except:
                    pass
                    
    except websockets.exceptions.ConnectionClosed:
        print(f"A2A client disconnected: {websocket.remote_address}")
        if client_agent_id and client_agent_id in a2a_server.agents:
            a2a_server.agents[client_agent_id].status = "offline"
            print(f"Marked agent {client_agent_id} as offline")
    except Exception as e:
        print(f"A2A connection error: {e}")
        if client_agent_id and client_agent_id in a2a_server.agents:
            a2a_server.agents[client_agent_id].status = "offline"
            print(f"Marked agent {client_agent_id} as offline due to error")

async def start_a2a_server():
    print("Starting Fixed A2A Server on ws://localhost:9090")
    try:
        server = await websockets.serve(
            handle_a2a_client, 
            "localhost", 
            9090,
            ping_interval=30,
            ping_timeout=20,
            close_timeout=10,
            max_size=2**20,
            compression=None
        )
        print("Fixed A2A Server is running and ready for connections")
        await asyncio.Future()
    except Exception as e:
        print(f"A2A Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(start_a2a_server())
    except KeyboardInterrupt:
        print("A2A Server stopped by user")
    except Exception as e:
        print(f"A2A Server failed to start: {e}")
        print("Please check if port 9090 is available")
