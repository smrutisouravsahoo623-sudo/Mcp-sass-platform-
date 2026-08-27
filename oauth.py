"""
Minimal OAuth2 Authorization Code flow (Google as example provider).
On successful login we issue our OWN long-lived API token that the
MCP client will present on every request (Authorization: Bearer <token>).
"""
import os
import secrets
import hashlib
import datetime as dt

import requests
from starlette.responses import RedirectResponse, JSONResponse
from starlette.requests import Request

from ..db.session import get_session
from ..db.models import User, APIToken

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = os.environ.get("OAUTH_REDIRECT_URI", "https://your-domain.com/auth/callback")

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# in-memory state store for CSRF protection (use Redis in real prod)
_pending_states = set()


def start_login() -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    _pending_states.add(state)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{AUTH_URL}?{query}")


async def handle_callback(request: Request) -> JSONResponse:
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if state not in _pending_states:
        return JSONResponse({"error": "invalid_state"}, status_code=400)
    _pending_states.discard(state)

    # exchange code for tokens
    token_resp = requests.post(TOKEN_URL, data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    })
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    userinfo = requests.get(
        USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = userinfo["email"]
    subject = userinfo["sub"]

    with get_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, oauth_provider="google", oauth_subject=subject)
            db.add(user)
            db.flush()  # get user.id before commit

        # issue our own API token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        api_token = APIToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=dt.datetime.utcnow() + dt.timedelta(days=90),
        )
        db.add(api_token)

    return JSONResponse({
        "message": "Login successful. Use this token as your MCP client's Bearer token.",
        "token": raw_token,
        "expires_in_days": 90,
    })


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
