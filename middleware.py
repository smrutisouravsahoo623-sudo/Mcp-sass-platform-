"""
Starlette middleware: validates the Bearer token on every request and
attaches the authenticated user's id to request.state.user_id.
This is what makes multi-tenancy enforceable downstream -- tools read
request.state.user_id, never a client-supplied user id.
"""
import datetime as dt

from starlette.requests import Request
from starlette.responses import JSONResponse

from ..db.session import get_session
from ..db.models import APIToken
from .oauth import hash_token
from .tenant import set_current_user

PUBLIC_PATHS = {"/auth/login", "/auth/callback", "/health"}


async def auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"error": "missing_bearer_token"}, status_code=401)

    raw_token = auth_header.removeprefix("Bearer ").strip()
    token_hash = hash_token(raw_token)

    with get_session() as db:
        token_row = db.query(APIToken).filter(
            APIToken.token_hash == token_hash,
            APIToken.revoked == False,  # noqa: E712
        ).first()

        if not token_row:
            return JSONResponse({"error": "invalid_token"}, status_code=401)

        if token_row.expires_at < dt.datetime.utcnow():
            return JSONResponse({"error": "token_expired"}, status_code=401)

        # attach tenant id for downstream tool handlers (both request.state
        # and contextvar, since FastMCP tool functions read the contextvar)
        request.state.user_id = token_row.user_id
        set_current_user(str(token_row.user_id))

    return await call_next(request)
