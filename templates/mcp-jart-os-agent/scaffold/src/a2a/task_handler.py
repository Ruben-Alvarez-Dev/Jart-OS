"""
A2A Protocol — Task Handler

Manages the A2A task lifecycle:
- Task creation (from remote agent)
- Task execution (delegates to MCP tools)
- Task completion/cancellation
- Message exchange within tasks
"""

import uuid
from datetime import datetime, timezone
from typing import Any


class TaskHandler:
    """Handles A2A task lifecycle per specification v1.0.0."""

    def __init__(self):
        self._tasks: dict[str, dict[str, Any]] = {}

    async def create_task(self, message: dict) -> dict:
        """
        Create a new A2A task from an incoming message.
        Returns task state per A2A spec.
        """
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "status": {"state": "submitted"},
            "messages": [message],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._tasks[task_id] = task
        return task

    async def get_task(self, task_id: str) -> dict | None:
        """Retrieve task by ID."""
        return self._tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> dict | None:
        """Cancel a running task."""
        task = self._tasks.get(task_id)
        if task:
            task["status"] = {"state": "canceled"}
        return task
