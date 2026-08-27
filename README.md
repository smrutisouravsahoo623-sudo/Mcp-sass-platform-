
mcp-saas-platform
A multi-tenant, remote MCP server (task manager domain) with OAuth2 login, per-tenant data isolation, rate limiting, CI/CD, and a client SDK.
Quickstart (local dev)
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="sqlite:///./dev.db"
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export OAUTH_REDIRECT_URI="http://localhost:8000/auth/callback"

uvicorn src.main:app --reload --port 8000
Then visit http://localhost:8000/auth/login to get a token, and use it in client-sdk/examples/quickstart.py.
Quickstart (Docker)
docker compose up --build
Run tests
cd server
pytest tests/ -v
Project structure
server/ — the MCP server itself (tools, auth, DB, tests)
client-sdk/ — Python SDK + example usage for consumers
docs/ — architecture, auth flow, API reference
scripts/ — DB seeding, load testing
.github/workflows/ — CI (test/lint) and CD (build/deploy)
infra/ — (add Terraform/nginx configs here for your target cloud)
Key features
OAuth2 login (Google) issuing our own revocable, hashed API tokens
Tenant isolation enforced structurally in the tool layer, not by convention
Per-user sliding-window rate limiting
Full test suite including a dedicated cross-tenant leak test
CI on every PR, CD on merge to main
Reusable client SDK for other consumers of the server
See docs/architecture.md for the full request flow diagram.
