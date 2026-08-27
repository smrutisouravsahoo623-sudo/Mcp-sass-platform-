"""
Critical test: proves cross-tenant data leakage is impossible.
Uses an in-memory sqlite DB and directly exercises the tool functions
with two different simulated user contexts.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from src.db.session import init_db, get_session
from src.db.models import Base, User
from src.auth.tenant import set_current_user
from src.tools.tasks import register_task_tools


class DummyMCP:
    """Collects registered tool functions so we can call them directly in tests."""
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


@pytest.fixture
def mcp():
    m = DummyMCP()
    register_task_tools(m)
    return m


def make_user(email: str) -> str:
    with get_session() as db:
        user = User(email=email)
        db.add(user)
        db.flush()
        return user.id


def test_user_cannot_see_other_users_tasks(mcp):
    user_a = make_user("a@example.com")
    user_b = make_user("b@example.com")

    set_current_user(user_a)
    mcp.tools["create_task"]("Task belonging to A")

    set_current_user(user_b)
    mcp.tools["create_task"]("Task belonging to B")

    # As user B, list_tasks should only return B's task
    tasks_b = mcp.tools["list_tasks"](None)
    assert len(tasks_b) == 1
    assert tasks_b[0]["title"] == "Task belonging to B"

    # Switch back to A -- should only see A's task
    set_current_user(user_a)
    tasks_a = mcp.tools["list_tasks"](None)
    assert len(tasks_a) == 1
    assert tasks_a[0]["title"] == "Task belonging to A"


def test_user_cannot_update_another_users_task(mcp):
    user_a = make_user("a2@example.com")
    user_b = make_user("b2@example.com")

    set_current_user(user_a)
    created = mcp.tools["create_task"]("A's private task")

    set_current_user(user_b)
    result = mcp.tools["update_task"](created["id"], "done")

    assert "error" in result
    assert result["error"] == "task_not_found_or_not_owned_by_you"
