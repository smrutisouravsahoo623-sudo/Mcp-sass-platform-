import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from src.db.session import init_db, get_session
from src.db.models import User
from src.auth.tenant import set_current_user
from src.tools.tasks import register_task_tools


class DummyMCP:
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


@pytest.fixture
def user_id():
    with get_session() as db:
        user = User(email="test@example.com")
        db.add(user)
        db.flush()
        uid = user.id
    set_current_user(uid)
    return uid


def test_create_and_list_task(mcp, user_id):
    created = mcp.tools["create_task"]("Write MCP tests", "cover tool logic")
    assert created["title"] == "Write MCP tests"
    assert created["status"] == "todo"

    tasks = mcp.tools["list_tasks"](None)
    assert len(tasks) == 1
    assert tasks[0]["id"] == created["id"]


def test_update_task_status(mcp, user_id):
    created = mcp.tools["create_task"]("Ship feature")
    updated = mcp.tools["update_task"](created["id"], "done")
    assert updated["status"] == "done"


def test_search_tasks(mcp, user_id):
    mcp.tools["create_task"]("Fix login bug", "auth is broken")
    mcp.tools["create_task"]("Write docs")

    results = mcp.tools["search_tasks"]("login")
    assert len(results) == 1
    assert "login" in results[0]["title"].lower()


def test_filter_by_status(mcp, user_id):
    t1 = mcp.tools["create_task"]("Task 1")
    mcp.tools["update_task"](t1["id"], "done")
    mcp.tools["create_task"]("Task 2")

    done_tasks = mcp.tools["list_tasks"]("done")
    assert len(done_tasks) == 1
    assert done_tasks[0]["title"] == "Task 1"
