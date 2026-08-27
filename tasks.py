"""
Task management tools. Every query filters by tenant_id == current
authenticated user, sourced from the request-scoped contextvar -- never
from a client-supplied argument. This is what prevents cross-tenant
data leaks even if a caller tries to pass someone else's id.
"""
from typing import Optional

from ..db.session import get_session
from ..db.models import Task, TaskStatus
from ..auth.tenant import get_current_user


def register_task_tools(mcp):

    @mcp.tool()
    def create_task(title: str, description: str = "") -> dict:
        """Create a new task for the authenticated user"""
        tenant_id = get_current_user()
        with get_session() as db:
            task = Task(tenant_id=tenant_id, title=title, description=description)
            db.add(task)
            db.flush()
            return {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
            }

    @mcp.tool()
    def list_tasks(status: Optional[str] = None) -> list[dict]:
        """List tasks belonging to the authenticated user, optionally filtered by status"""
        tenant_id = get_current_user()
        with get_session() as db:
            query = db.query(Task).filter(Task.tenant_id == tenant_id)
            if status:
                query = query.filter(Task.status == TaskStatus(status))
            tasks = query.order_by(Task.created_at.desc()).all()
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ]

    @mcp.tool()
    def update_task(task_id: str, status: str) -> dict:
        """Update a task's status. Only the owning tenant can update their own task."""
        tenant_id = get_current_user()
        with get_session() as db:
            task = db.query(Task).filter(
                Task.id == task_id, Task.tenant_id == tenant_id
            ).first()
            if not task:
                return {"error": "task_not_found_or_not_owned_by_you"}
            task.status = TaskStatus(status)
            return {"id": task.id, "status": task.status.value}

    @mcp.tool()
    def search_tasks(query: str) -> list[dict]:
        """Full-text search over the authenticated user's tasks (title + description)"""
        tenant_id = get_current_user()
        with get_session() as db:
            like = f"%{query}%"
            tasks = db.query(Task).filter(
                Task.tenant_id == tenant_id,
                (Task.title.ilike(like)) | (Task.description.ilike(like)),
            ).all()
            return [{"id": t.id, "title": t.title, "status": t.status.value} for t in tasks]
