"""A2A HTTP endpoints — JSON-RPC 2.0 over HTTP.

Serves the Agent Card and handles task lifecycle:
- GET  /.well-known/agent.json    — Agent Card discovery
- POST /a2a                       — Main JSON-RPC endpoint
- GET  /a2a/tasks/{task_id}       — Task status
- POST /a2a/tasks/{task_id}/cancel — Cancel task
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from aiohttp import web

from .agent_card import get_agent_card
from .task_handler import TaskHandler


class A2ARoutes:
    """A2A protocol HTTP routes following JSON-RPC 2.0 spec."""

    def __init__(self, task_handler: TaskHandler):
        self._handler = task_handler
        self._router = web.RouteTableDef()

    @property
    def routes(self) -> web.RouteTableDef:
        return self._router

    def register(self, app: web.Application) -> None:
        """Register A2A routes on the aiohttp app."""
        app.router.add_get("/.well-known/agent.json", self._handle_agent_card)
        app.router.add_post("/a2a", self._handle_jsonrpc)
        app.router.add_get("/a2a/tasks/{task_id}", self._handle_get_task)
        app.router.add_post("/a2a/tasks/{task_id}/cancel", self._handle_cancel_task)

    async def _handle_agent_card(self, request: web.Request) -> web.Response:
        """GET /.well-known/agent.json — Return the Agent Card."""
        card = get_agent_card()
        return web.json_response(card)

    async def _handle_jsonrpc(self, request: web.Request) -> web.Response:
        """POST /a2a — Main JSON-RPC 2.0 endpoint.

        Supported methods:
        - tasks/send: Send a new task to this agent
        - tasks/sendSubscribe: Send task with streaming response
        - tasks/get: Get task status
        - tasks/cancel: Cancel a task
        - message/send: Send a direct message
        """
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                self._error_response(None, -32700, "Parse error"),
                status=400,
            )

        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        req_id = body.get("id")

        if jsonrpc != "2.0":
            return web.json_response(
                self._error_response(req_id, -32600, "Invalid Request: jsonrpc must be '2.0'"),
                status=400,
            )

        if not method:
            return web.json_response(
                self._error_response(req_id, -32600, "Invalid Request: method required"),
                status=400,
            )

        # Route to handler
        method_map = {
            "tasks/send": self._handle_tasks_send,
            "tasks/sendSubscribe": self._handle_tasks_send_subscribe,
            "tasks/get": self._handle_tasks_get,
            "tasks/cancel": self._handle_tasks_cancel,
            "message/send": self._handle_message_send,
        }

        handler = method_map.get(method)
        if not handler:
            return web.json_response(
                self._error_response(req_id, -32601, f"Method not found: {method}"),
                status=400,
            )

        result = await handler(params)
        return web.json_response(self._success_response(req_id, result))

    async def _handle_tasks_send(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/send — Create or update a task."""
        task_id = params.get("id", str(uuid.uuid4()))
        message = params.get("message", {})
        history_length = params.get("historyLength", 0)
        metadata = params.get("metadata", {})

        task = await self._handler.handle_task(
            task_id=task_id,
            message=message,
            history_length=history_length,
            metadata=metadata,
        )
        return task

    async def _handle_tasks_send_subscribe(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/sendSubscribe — Streaming variant (returns initial state)."""
        # For now, delegate to send. Full SSE streaming is a future enhancement.
        return await self._handle_tasks_send(params)

    async def _handle_tasks_get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/get — Retrieve task status."""
        task_id = params.get("id")
        if not task_id:
            return {"error": {"code": -32602, "message": "Missing task id"}}

        task = await self._handler.get_task(task_id)
        return task

    async def _handle_tasks_cancel(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tasks/cancel — Cancel a running task."""
        task_id = params.get("id")
        if not task_id:
            return {"error": {"code": -32602, "message": "Missing task id"}}

        task = await self._handler.cancel_task(task_id)
        return task

    async def _handle_message_send(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle message/send — Direct message to the agent."""
        message = params.get("message", {})
        # Process as a simple task
        task_id = str(uuid.uuid4())
        task = await self._handler.handle_task(
            task_id=task_id,
            message=message,
            history_length=0,
            metadata=params.get("metadata", {}),
        )
        return task

    async def _handle_get_task(self, request: web.Request) -> web.Response:
        """GET /a2a/tasks/{task_id} — Get task by ID."""
        task_id = request.match_info["task_id"]
        task = await self._handler.get_task(task_id)
        if not task:
            return web.json_response(
                {"error": "Task not found"}, status=404
            )
        return web.json_response(task)

    async def _handle_cancel_task(self, request: web.Request) -> web.Response:
        """POST /a2a/tasks/{task_id}/cancel — Cancel task."""
        task_id = request.match_info["task_id"]
        task = await self._handler.cancel_task(task_id)
        if not task:
            return web.json_response(
                {"error": "Task not found"}, status=404
            )
        return web.json_response(task)

    @staticmethod
    def _success_response(req_id: str | None, result: Any) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    @staticmethod
    def _error_response(
        req_id: str | None, code: int, message: str
    ) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
