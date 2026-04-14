"""
Jart-OS Agent Base — Core module v2.0
Every agent inherits from this class.

Messaging: NATS JetStream (all inter-agent comms)
State:     Redis (cache, locks, task state)
LLM:       LiteLLM proxy (gateway to all models)
HTTP:      Health, metrics, state endpoints
"""

import os
import json
import time
import logging
import asyncio
import requests
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)


class AgentHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for health, metrics, and state endpoints."""

    def do_GET(self):
        agent = self.server.agent
        if self.path in ("/health", "/", "/state"):
            body = json.dumps({
                "status": "ok",
                "role": agent.role,
                "domain": agent.domain,
                "tier": agent.tier,
                "started_at": agent.started_at,
                "tasks_completed": agent.tasks_completed,
                "tasks_failed": agent.tasks_failed,
                "current_task": agent.current_task,
                "nats_connected": agent.nc is not None,
                "redis_connected": agent.redis is not None,
            }, indent=2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(agent.format_metrics().encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


class AgentBase(ABC):
    """
    Base class for all Jart-OS agents.

    Every agent has:
      - A role (director, executor, guardian, council)
      - A domain (study, dev, infra, ...)
      - A tier number
      - NATS connection for ALL messaging
      - Redis connection for state/cache/locks
      - LiteLLM connection for LLM calls
      - HTTP server for health + metrics
      - A run loop with abstract method
    """

    def __init__(self, role: str, domain: str = "study", tier: int = 4):
        self.role = role
        self.domain = domain
        self.tier = tier
        self.started_at = datetime.now().isoformat()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.current_task = None
        self.uptime_start = time.time()

        self.log = logging.getLogger(f"jart-os.{domain}.{role}")

        # Environment
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:10302")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:10301")
        self.litellm_url = os.getenv("LITELLM_URL", "http://localhost:10201")
        self.litellm_key = os.getenv("LITELLM_KEY", "REDACTED_LITELLM_MASTER_KEY")
        self.port = int(os.getenv("AGENT_PORT", "8080"))
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")

        # NATS subject prefix: jart-os.<tier>.<domain>.<role>
        self.subject_prefix = f"jart-os.{tier:02d}.{domain}.{role}"

        # Connections
        self.nc = None       # NATS client
        self.js = None       # NATS JetStream context
        self.redis = None    # Redis client
        self._loop = None    # Async event loop

        # Connect
        self._connect_redis()
        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._connect_nats())

    # =================================================================
    # NATS — Primary messaging
    # =================================================================

    async def _connect_nats(self):
        """Connect to NATS JetStream."""
        try:
            import nats
            self.nc = await nats.connect(
                servers=[self.nats_url],
                name=f"jart-os-{self.domain}-{self.role}",
                reconnect_time_wait=2,
                max_reconnects=10,
            )
            self.js = self.nc.jetstream()
            self.log.info(f"NATS connected: {self.nats_url}")
        except ImportError:
            self.log.warning("nats-py not installed. pip install nats-py")
        except Exception as e:
            self.log.warning(f"NATS offline: {e}")

    async def nats_publish(self, subject: str, data: dict):
        """Publish message to NATS subject."""
        if self.nc:
            payload = json.dumps(data).encode()
            await self.nc.publish(subject, payload)
            self.log.debug(f"→ {subject}: {data.get('task_id', '?')}")

    async def nats_request(self, subject: str, data: dict, timeout: float = 30.0) -> dict:
        """Request-reply pattern. Waits for response."""
        if self.nc:
            payload = json.dumps(data).encode()
            try:
                response = await self.nc.request(subject, payload, timeout=timeout)
                return json.loads(response.data.decode())
            except asyncio.TimeoutError:
                self.log.error(f"Timeout waiting for reply on {subject}")
                return {"error": "timeout"}
        return {"error": "nats not connected"}

    async def nats_subscribe(self, subject: str, handler):
        """Subscribe to NATS subject with async handler."""
        if self.nc:
            await self.nc.subscribe(subject, cb=handler)
            self.log.info(f"Subscribed to: {subject}")

    # =================================================================
    # Convenience methods (sync wrappers for use in non-async code)
    # =================================================================

    def publish(self, subject: str, data: dict):
        """Sync wrapper: publish to NATS."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.nats_publish(subject, data), self._loop
            )
        elif self._loop:
            self._loop.run_until_complete(self.nats_publish(subject, data))

    def request(self, subject: str, data: dict, timeout: float = 30.0) -> dict:
        """Sync wrapper: request-reply on NATS."""
        if self._loop:
            return self._loop.run_until_complete(
                self.nats_request(subject, data, timeout)
            )
        return {"error": "no event loop"}

    # =================================================================
    # Subject helpers
    # =================================================================

    @property
    def subject_command(self) -> str:
        """Subject this agent listens to for commands."""
        return f"{self.subject_prefix}.command"

    @property
    def subject_events(self) -> str:
        """Subject this agent publishes events to."""
        return f"{self.subject_prefix}.events"

    @property
    def subject_errors(self) -> str:
        """Subject this agent publishes errors to."""
        return f"{self.subject_prefix}.errors"

    def domain_subject(self, role: str, action: str) -> str:
        """Build subject for another agent in same domain."""
        return f"jart-os.{self.tier:02d}.{self.domain}.{role}.{action}"
