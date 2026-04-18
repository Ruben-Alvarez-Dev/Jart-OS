"""Observability endpoints — Health, Metrics, State.

Follows AgentBase v3.0 pattern from agents/core/base.py.
HTTP endpoints exposed for monitoring and debugging.

Endpoints:
- GET /health  — {status, role, domain, tier, uptime}
- GET /metrics — Prometheus-format metrics
- GET /state   — {tasks_completed, tasks_failed, current_task, connections, uptime}
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from aiohttp import web


@dataclass
class ObservabilityConfig:
    """Configuration for observability endpoints."""

    role: str = "backpack"
    domain: str = "{function}"
    tier: int = 4
    service_name: str = "MCP-jart-os-agent-{function}"
    health_port: int = 0  # 0 = auto-assign


@dataclass
class ServiceMetrics:
    """In-memory metrics for the service."""

    start_time: float = field(default_factory=time.time)
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_in_progress: int = 0
    current_task: str | None = None
    nats_connected: bool = False
    redis_connected: bool = False
    total_tool_calls: int = 0
    total_errors: int = 0


class ObservabilityServer:
    """Lightweight HTTP server for health/metrics/state endpoints."""

    def __init__(self, config: ObservabilityConfig):
        self.config = config
        self.metrics = ServiceMetrics()
        self._app = web.Application()
        self._register_routes()

    def _register_routes(self) -> None:
        self._app.router.add_get("/health", self._handle_health)
        self._app.router.add_get("/metrics", self._handle_metrics)
        self._app.router.add_get("/state", self._handle_state)

    @property
    def app(self) -> web.Application:
        return self._app

    def get_runner(self, port: int | None = None) -> web.AppRunner:
        """Create an AppRunner for embedding in another server."""
        runner = web.AppRunner(self._app)
        return runner

    async def _handle_health(self, request: web.Request) -> web.Response:
        """GET /health — Service health status."""
        uptime = time.time() - self.metrics.start_time
        healthy = self.metrics.nats_connected and self.metrics.redis_connected

        return web.json_response({
            "status": "healthy" if healthy else "degraded",
            "service": self.config.service_name,
            "role": self.config.role,
            "domain": self.config.domain,
            "tier": self.config.tier,
            "uptime_seconds": round(uptime, 2),
            "connections": {
                "nats": "connected" if self.metrics.nats_connected else "disconnected",
                "redis": "connected" if self.metrics.redis_connected else "disconnected",
            },
        })

    async def _handle_metrics(self, request: web.Request) -> web.Response:
        """GET /metrics — Prometheus-format metrics."""
        uptime = time.time() - self.metrics.start_time
        lines = [
            f"# HELP jart_os_tasks_completed Total tasks completed",
            f"# TYPE jart_os_tasks_completed counter",
            f"jart_os_tasks_completed{{service=\"{self.config.service_name}\"}} {self.metrics.tasks_completed}",
            "",
            f"# HELP jart_os_tasks_failed Total tasks failed",
            f"# TYPE jart_os_tasks_failed counter",
            f"jart_os_tasks_failed{{service=\"{self.config.service_name}\"}} {self.metrics.tasks_failed}",
            "",
            f"# HELP jart_os_tasks_in_progress Currently running tasks",
            f"# TYPE jart_os_tasks_in_progress gauge",
            f"jart_os_tasks_in_progress{{service=\"{self.config.service_name}\"}} {self.metrics.tasks_in_progress}",
            "",
            f"# HELP jart_os_tool_calls Total MCP tool invocations",
            f"# TYPE jart_os_tool_calls counter",
            f"jart_os_tool_calls{{service=\"{self.config.service_name}\"}} {self.metrics.total_tool_calls}",
            "",
            f"# HELP jart_os_errors Total errors encountered",
            f"# TYPE jart_os_errors counter",
            f"jart_os_errors{{service=\"{self.config.service_name}\"}} {self.metrics.total_errors}",
            "",
            f"# HELP jart_os_uptime_seconds Service uptime in seconds",
            f"# TYPE jart_os_uptime_seconds gauge",
            f"jart_os_uptime_seconds{{service=\"{self.config.service_name}\"}} {round(uptime, 2)}",
            "",
        ]
        return web.Response(
            text="\n".join(lines),
            content_type="text/plain; version=0.0.4",
        )

    async def _handle_state(self, request: web.Request) -> web.Response:
        """GET /state — Detailed service state."""
        uptime = time.time() - self.metrics.start_time
        return web.json_response({
            "service": self.config.service_name,
            "role": self.config.role,
            "domain": self.config.domain,
            "tier": self.config.tier,
            "uptime_seconds": round(uptime, 2),
            "tasks": {
                "completed": self.metrics.tasks_completed,
                "failed": self.metrics.tasks_failed,
                "in_progress": self.metrics.tasks_in_progress,
                "current": self.metrics.current_task,
            },
            "connections": {
                "nats": self.metrics.nats_connected,
                "redis": self.metrics.redis_connected,
            },
            "totals": {
                "tool_calls": self.metrics.total_tool_calls,
                "errors": self.metrics.total_errors,
            },
        })

    def record_task_start(self, task_id: str) -> None:
        """Record a task starting."""
        self.metrics.tasks_in_progress += 1
        self.metrics.current_task = task_id

    def record_task_complete(self) -> None:
        """Record a task completing successfully."""
        self.metrics.tasks_completed += 1
        self.metrics.tasks_in_progress = max(0, self.metrics.tasks_in_progress - 1)
        if self.metrics.tasks_in_progress == 0:
            self.metrics.current_task = None

    def record_task_failure(self) -> None:
        """Record a task failing."""
        self.metrics.tasks_failed += 1
        self.metrics.total_errors += 1
        self.metrics.tasks_in_progress = max(0, self.metrics.tasks_in_progress - 1)
        if self.metrics.tasks_in_progress == 0:
            self.metrics.current_task = None

    def record_tool_call(self) -> None:
        """Record a tool invocation."""
        self.metrics.total_tool_calls += 1

    def set_connection_status(self, nats: bool, redis: bool) -> None:
        """Update connection status."""
        self.metrics.nats_connected = nats
        self.metrics.redis_connected = redis
