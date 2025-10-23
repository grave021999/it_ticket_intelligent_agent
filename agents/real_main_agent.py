import asyncio
import websockets
import json
import time

class MainAgent:
    def __init__(self):
        self.agent_id = "main_agent"
        self.name = "Main Agent"
        self.a2a_server = "ws://localhost:9090"
        self.a2a_ws = None
        self.agents = {}
        self.task_responses = {}

    async def connect_a2a(self):
        try:
            self.a2a_ws = await websockets.connect(self.a2a_server)
            reg = {
                "type": "agent_register",
                "agent_id": self.agent_id,
                "name": self.name,
                "capabilities": [
                    "orchestration",
                    "query_processing",
                    "task_delegation",
                    "user_interface",
                ],
                "endpoint": "ws://localhost:9100",
            }
            await self.a2a_ws.send(json.dumps(reg))
            print("Registered Main Agent on A2A")

            asyncio.create_task(self.listen_a2a())

            await self.a2a_ws.send(json.dumps({"type": "discover_agents"}))
        except Exception as e:
            print("Failed to connect to A2A:", e)

    async def listen_a2a(self):
        print("Listening for A2A messages...")
        try:
            while True:
                msg = await self.a2a_ws.recv()
                data = json.loads(msg)

                if data.get("status") == "success" and data.get("agents"):
                    for a in data["agents"]:
                        self.agents[a["agent_id"]] = a
                    print("Agents discovered:", list(self.agents.keys()))

                elif data.get("type") == "task_completed":
                    self.task_responses[data["task_id"]] = data
                    print(f"Task completed from {data.get('from_agent')}")

        except websockets.ConnectionClosed:
            print("A2A connection lost — reconnecting...")
            await asyncio.sleep(2)
            await self.connect_a2a()

    async def delegate_task(self, query: str):
        analytics = [a for a in self.agents if "analytics_agent" in a]
        if not analytics:
            print("No analytics agent found.")
            return None

        target = analytics[0]
        task_id = str(int(time.time()))
        task = {
            "type": "delegate_task",
            "from_agent": self.agent_id,
            "to_agent": target,
            "task_id": task_id,
            "task_type": "trend_analysis",
            "payload": {"query": query},
        }

        await self.a2a_ws.send(json.dumps(task))
        print(f"Sent task '{query}' to {target}")

        for _ in range(20):
            if task_id in self.task_responses:
                result = self.task_responses[task_id]["result"]
                print("Received result:", json.dumps(result, indent=2))
                return result
            await asyncio.sleep(1)

        print("⏰ Timeout waiting for Analytics Agent response.")
        return None

    async def run(self):
        await self.connect_a2a()
        await asyncio.sleep(2)

        while True:
            query = input("\nYour query: ")
            if query.lower() == "exit":
                break
            result = await self.delegate_task(query)
            if result:
                print("\nAnalysis Result:")
                print(result["summary"])
            else:
                print("No response received.")


if __name__ == "__main__":
    main = MainAgent()
    asyncio.run(main.run())
