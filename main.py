"""
Entrypoint for the multi-tenant MCP SaaS server.

Run locally:
    uvicorn src.main:app --reload --port 8000

Run in prod (behind nginx/Caddy terminating TLS):
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
"""
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request

from .db.session import init_db
from .tools.tasks import register_task_tools
from .auth.middleware import auth_middleware
from .auth.oauth import start_login, handle_callback
from .rate_limit import rate_limit_middleware

# ---- Build the MCP server + register tools ----
mcp = FastMCP("mcp-saas-platform")
register_task_tools(mcp)

# ---- Underlying Starlette app from FastMCP (streamable HTTP transport) ----
mcp_app = mcp.streamable_http_app()


# ---- Auth routes (not part of MCP protocol, plain HTTP) ----
async def login_route(request: Request):
    return start_login()


async def callback_route(request: Request):
    return await handle_callback(request)


async def health_route(request: Request):
    return JSONResponse({"status": "ok"})


routes = [
    Route("/auth/login", login_route),
    Route("/auth/callback", callback_route),
    Route("/health", health_route),
]

app = Starlette(routes=routes)
app.mount("/mcp", mcp_app)  # actual MCP protocol endpoint lives at /mcp

# ---- Middleware order matters: Starlette runs the LAST-added middleware
#      FIRST. We want auth to run before rate limiting (so rate limits key
#      off the authenticated user_id), so auth is added last. ----
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402

app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)


@app.on_event("startup")
def on_startup():
    init_db()
