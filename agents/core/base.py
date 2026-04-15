"""
Jart-OS Agent Base — Core module v3.0
Every agent inherits from this class.

Spec references:
  §11 — Agent Architecture (Base Class, HTTP, LLM, Lifecycle)
  §12 — Communication Backbone (NATS subjects, Message Envelope, Redis Role)
  §14 — Policy Gates (Audit Trail Layer C)
  §10 — LLM Routing Strategy (Model→Role Mapping)
  §6  — Port Convention (1XXYY)

Messaging: NATS JetStream (all inter-agent comms) — §24 D3
State:     Redis (cache, locks, task state) — §12 "Redis Role"
LLM:       LiteLLM proxy (gateway to all models) — §10, §11
HTTP:      Health, metrics, state endpoints — §11 "HTTP server"
"""

import os
import json
import time
import signal
import logging
import asyncio
import requests
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)


class AgentHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for health, metrics, and state endpoints. — §11 'HTTP server'"""

    def do_GET(self):
        agent = self.server.agent
        if self.path in ("/health", "/", "/state"):
            body = json.dumps(
                {
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
                },
                indent=2,
            )
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
    Base class for all Jart-OS agents. — §11 'Agent Architecture > Base Class'

    Every agent has:
      - A role (director, executor, guardian, council)
      - A domain (study, dev, infra, ...)
      - A tier number
      - NATS connection for ALL messaging — §24 D3
      - Redis connection for state/cache/locks — §12 'Redis Role'
      - LiteLLM connection for LLM calls — §11 'LLM calls'
      - HTTP server for health + metrics — §11 'HTTP server'
      - A run loop with abstract method — §11 'Lifecycle'
    """

    def __init__(self, role: str, domain: str = "study", tier: int = 4):
        self.role = role
        self.domain = domain
        self.tier = tier
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.current_task = None
        self.uptime_start = time.time()

        self.log = logging.getLogger(f"jart-os.{domain}.{role}")

        # Environment — §6 port convention, §20 stack
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:10302")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:10301")
        self.litellm_url = os.getenv("LITELLM_URL", "http://localhost:10201")
        self.litellm_key = os.getenv("LITELLM_KEY", "REDACTED_LITELLM_MASTER_KEY")
        self.port = int(os.getenv("AGENT_PORT", "10400"))  # §6 default in 104YY range
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")

        # NATS subject prefix: jart-os.<tier>.<domain>.<role> — §12 'Subject Taxonomy'
        self.subject_prefix = f"jart-os.{tier:02d}.{domain}.{role}"

        # Connections
        self.nc = None  # NATS client
        self.js = None  # NATS JetStream context
        self.redis = None  # Redis client
        self._loop = None  # Async event loop
        self._http_server = None
        self._running = False

    # =================================================================
    # Lifecycle — §11 'Lifecycle: boot() → connect NATS + Redis + HTTP → run()'
    # =================================================================

    def boot(self):
        """
        Boot sequence: connect NATS → connect Redis → start HTTP → run().
        — §11 'boot() → HTTP thread + run() abstract method'
        """
        self.log.info(
            f"Booting agent: {self.role} domain={self.domain} tier={self.tier}"
        )

        # 1. Connect Redis — §12 'Redis Role'
        self._connect_redis()

        # 2. Connect NATS — §12 'Communication Backbone (NATS)'
        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._connect_nats())

        # 3. Start HTTP server — §11 'HTTP server'
        self._start_http()

        # 4. Register shutdown handlers — §11 lifecycle
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self._running = True
        self.log.info(f"Agent booted. HTTP on :{self.port}")

        # 5. Enter run loop — §11 'run() abstract method'
        try:
            self.run()
        except KeyboardInterrupt:
            self.log.info("Interrupted by user")
        finally:
            self._shutdown()

    @abstractmethod
    def run(self):
        """Main agent loop. Subclasses MUST implement. — §11 'run() abstract method'"""
        pass

    def _signal_handler(self, signum, frame):
        """Graceful shutdown on SIGTERM/SIGINT. — §11 lifecycle"""
        self.log.info(f"Received signal {signum}, shutting down...")
        self._running = False

    def _shutdown(self):
        """Drain connections and stop. — §11 lifecycle"""
        self.log.info("Shutting down agent...")
        if self.nc:
            try:
                self._loop.run_until_complete(self.nc.drain())
            except Exception:
                pass
        if self.redis:
            try:
                self.redis.close()
            except Exception:
                pass
        if self._http_server:
            pass  # HTTP server runs in daemon thread
        self.log.info("Agent shutdown complete")

    # =================================================================
    # NATS — Primary messaging — §12 'Communication Backbone (NATS)'
    # =================================================================

    async def _connect_nats(self):
        """Connect to NATS JetStream. — §12 'JetStream'"""
        try:
            import nats
            from urllib.parse import urlparse

            # Parse NATS_URL — handle token://token:PASS@host:port format
            parsed = urlparse(self.nats_url)
            nats_host = parsed.hostname or "nats"
            nats_port = parsed.port or 4222
            server_url = f"nats://{nats_host}:{nats_port}"

            # Extract auth token from URL password field or NATS_TOKEN env
            nats_token = parsed.password or os.getenv("NATS_TOKEN")

            connect_kwargs = dict(
                servers=[server_url],
                name=f"jart-os-{self.domain}-{self.role}",
                reconnect_time_wait=2,
                max_reconnect_attempts=10,
            )
            if nats_token:
                connect_kwargs["token"] = nats_token

            self.nc = await nats.connect(**connect_kwargs)
            self.js = self.nc.jetstream()
            self.log.info(f"NATS connected: {server_url}")
        except ImportError:
            self.log.warning("nats-py not installed. pip install nats-py")
        except Exception as e:
            self.log.warning(f"NATS offline: {e}")

    async def nats_publish(self, subject: str, data: dict):
        """Publish message to NATS subject. — §12"""
        if self.nc:
            payload = json.dumps(data).encode()
            await self.nc.publish(subject, payload)
            self.log.debug(f"→ {subject}: {data.get('task_id', '?')}")

    async def nats_request(
        self, subject: str, data: dict, timeout: float = 30.0
    ) -> dict:
        """Request-reply pattern. — §12"""
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
        """Subscribe to NATS subject with async handler. — §12"""
        if self.nc:
            await self.nc.subscribe(subject, cb=handler)
            self.log.info(f"Subscribed to: {subject}")

    # =================================================================
    # Sync wrappers — for use in non-async run() implementations
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
    # Subject helpers — §12 'Subject Taxonomy'
    # =================================================================

    @property
    def subject_command(self) -> str:
        """Subject this agent listens to for commands. — §12"""
        return f"{self.subject_prefix}.command"

    @property
    def subject_events(self) -> str:
        """Subject this agent publishes events to. — §12"""
        return f"{self.subject_prefix}.events"

    @property
    def subject_errors(self) -> str:
        """Subject this agent publishes errors to. — §12"""
        return f"{self.subject_prefix}.errors"

    def domain_subject(self, role: str, action: str) -> str:
        """Build subject for another agent in same domain. — §12"""
        return f"jart-os.{self.tier:02d}.{self.domain}.{role}.{action}"

    # =================================================================
    # LLM calls — §11 'LLM calls: Via LiteLLM proxy (call_llm() method)'
    #             §10 'LLM Routing Strategy'
    # =================================================================

    def call_llm(
        self,
        model: str,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict:
        """
        Call LLM via LiteLLM proxy. — §11 'LLM calls', §10 'Through LiteLLM :10201'

        Args:
            model: Model name (glm-5, glm-4.7, phi3-local, etc.) — §10
            messages: Chat messages list [{"role": "user", "content": "..."}]
            temperature: Sampling temp — §10 'Model→Role Mapping'
            max_tokens: Max response tokens

        Returns:
            dict with 'choices' or 'error'
        """
        try:
            response = requests.post(
                f"{self.litellm_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.litellm_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            self.log.error(f"LLM timeout: model={model}")
            return {"error": "timeout", "model": model}
        except requests.exceptions.RequestException as e:
            self.log.error(f"LLM error: {e}")
            return {"error": str(e), "model": model}

    def call_llm_text(
        self,
        model: str,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Convenience: call LLM and return text content directly."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        result = self.call_llm(model, messages, temperature, max_tokens)
        if "error" in result:
            return f"ERROR: {result['error']}"
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "ERROR: unexpected LLM response format"

    # =================================================================
    # Redis — §12 'Redis Role (State, Not Messaging)'
    #         Key patterns: jart-os:task:<id>, jart-os:agent:<role>,
    #                       jart-os:lock:<resource>, jart-os:cache:<hash>,
    #                       jart-os:ratelimit:<agent>, jart-os:audit:<id>
    # =================================================================

    def _connect_redis(self):
        """Connect to Redis for state/cache/locks. — §12 'Redis Role'"""
        try:
            import redis

            self.redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
            )
            self.redis.ping()
            self.log.info(f"Redis connected: {self.redis_url}")
        except ImportError:
            self.log.warning("redis-py not installed. pip install redis")
        except Exception as e:
            self.log.warning(f"Redis offline: {e}")

    def redis_set(self, key: str, value, ttl: int = None):
        """Set Redis key with optional TTL. — §12 'Cache'"""
        if self.redis:
            full_key = f"jart-os:{key}"
            data = json.dumps(value) if isinstance(value, (dict, list)) else value
            if ttl:
                self.redis.setex(full_key, ttl, data)
            else:
                self.redis.set(full_key, data)

    def redis_get(self, key: str):
        """Get Redis key value. — §12"""
        if self.redis:
            full_key = f"jart-os:{key}"
            data = self.redis.get(full_key)
            if data:
                try:
                    return json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    return data
        return None

    def redis_lock(self, resource: str, ttl: int = 30):
        """Acquire distributed lock. — §12 'Locks: jart-os:lock:<resource>'"""
        if self.redis:
            lock_key = f"jart-os:lock:{resource}"
            # Simple SET NX with expiry
            acquired = self.redis.set(lock_key, self.role, nx=True, ex=ttl)
            return bool(acquired)
        return False

    def redis_unlock(self, resource: str):
        """Release distributed lock."""
        if self.redis:
            lock_key = f"jart-os:lock:{resource}"
            self.redis.delete(lock_key)

    def redis_heartbeat(self):
        """Update agent heartbeat in Redis. — §12 'Agent heartbeat: jart-os:agent:<role>'"""
        if self.redis:
            self.redis_set(
                f"agent:{self.role}",
                {
                    "status": "running",
                    "domain": self.domain,
                    "tier": self.tier,
                    "tasks_completed": self.tasks_completed,
                    "tasks_failed": self.tasks_failed,
                    "current_task": self.current_task,
                    "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                },
                ttl=60,
            )

    def audit_log(self, task_id: str, data: dict):
        """Write audit trail to Redis. — §14 Layer C 'Audit Trail (Always)'"""
        if self.redis:
            self.redis_set(
                f"audit:{task_id}",
                {
                    **data,
                    "agent": self.role,
                    "domain": self.domain,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

    # =================================================================
    # Message Envelope — §12 'Message Envelope (Standard)'
    # =================================================================

    def build_envelope(
        self,
        objective: str,
        spec: dict = None,
        success_criteria: list = None,
        model_hint: str = None,
        context: dict = None,
        priority: str = "normal",
        max_retries: int = 3,
        timeout_seconds: int = 120,
    ) -> dict:
        """
        Build standard message envelope. — §12 'Message Envelope' JSON

        Required fields per §14 Layer A: task_id, objective, criteria,
        max_retries, timeout.
        """
        task_id = f"{self.domain.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.role}"
        return {
            "task_id": task_id,
            "from": f"{self.role}-{self.domain}",
            "to": "",  # Set by caller
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": priority,
            "retry_count": 0,
            "max_retries": max_retries,
            "timeout_seconds": timeout_seconds,
            "payload": {
                "objective": objective,
                "spec": spec or {},
                "success_criteria": success_criteria or [],
                "model_hint": model_hint or "",
                "context": context or {},
            },
        }

    # =================================================================
    # HTTP Server — §11 'HTTP server: Health, metrics, state endpoints'
    # =================================================================

    def _start_http(self):
        """Start HTTP server in background thread. — §11"""
        server = HTTPServer(("0.0.0.0", self.port), AgentHTTPHandler)
        server.agent = self
        self._http_server = server
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.log.info(f"HTTP server on :{self.port}")

    def format_metrics(self) -> str:
        """Prometheus-format metrics. — §11 'Metrics'"""
        uptime = int(time.time() - self.uptime_start)
        m = "# TYPE jart_os_agent_info gauge\n"
        m += f'jart_os_agent_info{{role="{self.role}",domain="{self.domain}",tier="{self.tier}"}} 1\n'
        m += "# TYPE jart_os_tasks_completed counter\n"
        m += f'jart_os_tasks_completed{{role="{self.role}"}} {self.tasks_completed}\n'
        m += "# TYPE jart_os_tasks_failed counter\n"
        m += f'jart_os_tasks_failed{{role="{self.role}"}} {self.tasks_failed}\n'
        m += "# TYPE jart_os_uptime_seconds gauge\n"
        m += f'jart_os_uptime_seconds{{role="{self.role}"}} {uptime}\n'
        m += "# TYPE jart_os_nats_connected gauge\n"
        m += f'jart_os_nats_connected{{role="{self.role}"}} {1 if self.nc else 0}\n'
        m += "# TYPE jart_os_redis_connected gauge\n"
        m += f'jart_os_redis_connected{{role="{self.role}"}} {1 if self.redis else 0}\n'
        return m

    # =================================================================
    # Notifications — §21 (DISCORD_WEBHOOK_URL)
    # =================================================================

    def notify_discord(self, message: str):
        """Send notification via Discord webhook. — §21"""
        if not self.discord_webhook:
            return
        try:
            requests.post(
                self.discord_webhook,
                json={"content": f"[{self.role}-{self.domain}] {message}"},
                timeout=10,
            )
        except Exception as e:
            self.log.warning(f"Discord notify failed: {e}")
