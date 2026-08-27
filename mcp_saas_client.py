"""
Thin client SDK wrapping the raw MCP streamable-HTTP client, so consumers
don't need to know MCP protocol details -- just call methods.

Usage:
    from mcp_saas_client import MCPSaaSClient

    client = MCPSaaSClient(base_url="https://your-domain.com/mcp", token="...")
    await client.connect()
    task = await client.create_task("Buy milk")
    tasks = await client.list_tasks()
"""
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPSaaSClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self._session: ClientSession | None = None
        self._ctx = None

    async def connect(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        self._ctx = streamablehttp_client(self.base_url, headers=headers)
        read, write, _ = await self._ctx.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()

    async def close(self):
        if self._session:
            await self._session.__aexit__(None, None, None)
        if self._ctx:
            await self._ctx.__aexit__(None, None, None)

    async def create_task(self, title: str, description: str = "") -> dict:
        result = await self._session.call_tool(
            "create_task", {"title": title, "description": description}
        )
        return result.content[0].text

    async def list_tasks(self, status: str | None = None) -> list:
        result = await self._session.call_tool("list_tasks", {"status": status})
        return result.content[0].text

    async def update_task(self, task_id: str, status: str) -> dict:
        result = await self._session.call_tool(
            "update_task", {"task_id": task_id, "status": status}
        )
        return result.content[0].text

    async def search_tasks(self, query: str) -> list:
        result = await self._session.call_tool("search_tasks", {"query": query})
        return result.content[0].text
