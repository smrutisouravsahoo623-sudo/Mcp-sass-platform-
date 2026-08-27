"""
Simple sliding-window rate limiter, per user_id.
For real production, swap the in-memory dict for Redis (INCR + EXPIRE)
so it works correctly across multiple server instances.
"""
import time
from collections import defaultdict, deque

from starlette.requests import Request
from starlette.responses import JSONResponse

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 120

_request_log: dict[str, deque] = defaultdict(deque)


async def rate_limit_middleware(request: Request, call_next):
    user_id = getattr(request.state, "user_id", None)
    key = str(user_id) if user_id else request.client.host  # fallback to IP pre-auth

    now = time.time()
    log = _request_log[key]

    while log and now - log[0] > WINDOW_SECONDS:
        log.popleft()

    if len(log) >= MAX_REQUESTS_PER_WINDOW:
        return JSONResponse(
            {"error": "rate_limit_exceeded", "retry_after_seconds": WINDOW_SECONDS},
            status_code=429,
        )

    log.append(now)
    return await call_next(request)
