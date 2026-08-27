"""
Quickstart: run this after you've logged in via /auth/login and obtained
a token from /auth/callback.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
from mcp_saas_client import MCPSaaSClient  # noqa: E402


async def main():
    client = MCPSaaSClient(
        base_url="http://localhost:8000/mcp",
        token="YOUR_TOKEN_FROM_OAUTH_LOGIN",
    )
    await client.connect()

    created = await client.create_task("Try out the MCP SaaS platform")
    print("Created:", created)

    tasks = await client.list_tasks()
    print("All tasks:", tasks)

    await client.update_task(created["id"], "done")
    done_tasks = await client.list_tasks(status="done")
    print("Done tasks:", done_tasks)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
