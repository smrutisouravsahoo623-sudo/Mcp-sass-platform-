# API Reference

## Auth (plain HTTP, not MCP)

| Route | Method | Description |
|---|---|---|
| `/auth/login` | GET | Redirects to Google OAuth consent screen |
| `/auth/callback` | GET | OAuth callback, returns your API token |
| `/health` | GET | Liveness check |

## MCP Tools (via `POST /mcp`, JSON-RPC `tools/call`)

### `create_task(title: str, description: str = "") -> dict`
Creates a task for the authenticated user.

### `list_tasks(status: str | None = None) -> list[dict]`
Lists the authenticated user's tasks. `status` one of `todo`, `in_progress`, `done`.

### `update_task(task_id: str, status: str) -> dict`
Updates a task's status. Returns an error if the task doesn't belong to you.

### `search_tasks(query: str) -> list[dict]`
Case-insensitive search over title + description.

## Example raw JSON-RPC call

```bash
curl -X POST https://your-domain.com/mcp \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "create_task", "arguments": { "title": "Ship it" } }
  }'
```
