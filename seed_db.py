"""
Seeds the local dev database with a test user and a few tasks.
Run with: python scripts/seed_db.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from src.db.session import init_db, get_session  # noqa: E402
from src.db.models import User, Task, TaskStatus  # noqa: E402


def seed():
    init_db()
    with get_session() as db:
        existing = db.query(User).filter(User.email == "dev@example.com").first()
        if existing:
            print("Dev user already exists:", existing.id)
            return

        user = User(email="dev@example.com")
        db.add(user)
        db.flush()

        db.add_all([
            Task(tenant_id=user.id, title="Set up local environment", status=TaskStatus.done),
            Task(tenant_id=user.id, title="Read the architecture docs", status=TaskStatus.todo),
            Task(tenant_id=user.id, title="Try the MCP tools from Claude", status=TaskStatus.todo),
        ])

        print(f"Seeded user {user.email} (id={user.id}) with 3 tasks.")


if __name__ == "__main__":
    seed()
