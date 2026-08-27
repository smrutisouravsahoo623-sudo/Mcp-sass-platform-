"""
Tenant context: FastMCP tool functions don't get direct access to the raw
Starlette `request` object, so we use a contextvar set by the middleware
(see middleware.py) and read here inside each tool. This guarantees every
tool call is scoped to the authenticated caller only -- there is no code
path where a tool can be called with an attacker-supplied tenant_id.
"""
from contextvars import ContextVar

current_user_id: ContextVar[str] = ContextVar("current_user_id", default=None)


def set_current_user(user_id: str):
    current_user_id.set(user_id)


def get_current_user() -> str:
    user_id = current_user_id.get()
    if user_id is None:
        raise PermissionError("No authenticated user in context")
    return user_id
