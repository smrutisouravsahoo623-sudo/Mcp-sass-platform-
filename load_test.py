"""
Locust load test for the /health and MCP tool-call endpoints.
Run with:
    locust -f scripts/load_test.py --host http://localhost:8000
"""
from locust import HttpUser, task, between


class MCPUser(HttpUser):
    wait_time = between(0.5, 2)
    token = "YOUR_TEST_TOKEN"

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def call_list_tasks(self):
        self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "list_tasks", "arguments": {"status": None}},
            },
            headers={"Authorization": f"Bearer {self.token}"},
        )
