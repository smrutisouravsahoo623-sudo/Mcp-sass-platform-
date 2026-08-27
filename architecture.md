# Architecture

```
                 ┌────────────────────┐
                 │   Claude / MCP      │
                 │   Client (any host) │
                 └─────────┬───────────┘
                            │ HTTPS (streamable HTTP, JSON-RPC 2.0)
                            │ Authorization: Bearer <token>
                            ▼
                 ┌────────────────────────────┐
                 │   nginx / Caddy (TLS term.) │
                 └─────────────┬──────────────┘
                                ▼
                 ┌────────────────────────────┐
                 │   Starlette app (main.py)   │
                 │  ┌──────────────────────┐   │
                 │  │ auth_middleware       │   │  validates Bearer token,
                 │  │ (runs first)          │   │  sets tenant context
                 │  └──────────┬────────────┘   │
                 │  ┌──────────▼────────────┐   │
                 │  │ rate_limit_middleware  │   │  per-user sliding window
                 │  └──────────┬────────────┘   │
                 │  ┌──────────▼────────────┐   │
                 │  │ FastMCP app (/mcp)     │   │  tools/list, tools/call
                 │  └──────────┬────────────┘   │
                 └─────────────┼────────────────┘
                                ▼
                 ┌────────────────────────────┐
                 │   Tool functions            │
                 │   (tasks.py, ...)            │  always scoped by
                 └─────────────┬────────────────┘  get_current_user()
                                ▼
                 ┌────────────────────────────┐
                 │   Postgres (tenant_id       │
                 │   indexed on every table)   │
                 └────────────────────────────┘
```

## Key design decisions

1. **Tenant scoping happens in the tool layer, not the client.** Tools never
   accept a `user_id` argument from the caller -- they always read it from
   `get_current_user()`, which is populated by the auth middleware from a
   verified, server-issued token. This makes cross-tenant data leaks a
   structural non-issue rather than something enforced by convention.

2. **Middleware order**: auth runs before rate limiting so that rate limits
   can be applied per authenticated user rather than per IP (which is easy
   to spoof/rotate).

3. **Our own token, not the raw OAuth token.** After the OAuth2 dance with
   Google, we issue our own opaque, hashed, revocable API token. This means
   we can revoke access without depending on the OAuth provider, and we
   never store the raw Google access token.

4. **SQLite fallback for local dev / CI.** `DATABASE_URL` defaults to a
   local sqlite file so contributors and CI don't need Postgres running to
   run the test suite.
