# Agent Development Guide

> Complete guide to building agents on the Jart-OS framework.

## Table of Contents

- [AgentBase API Reference](#agentbase-api-reference)
- [Creating a New Agent](#creating-a-new-agent)
- [Agent Lifecycle](#agent-lifecycle)
- [NATS Messaging Patterns](#nats-messaging-patterns)
- [Redis State Management](#redis-state-management)
- [LLM Calls via LiteLLM](#llm-calls-via-litellm)
- [HTTP Endpoints](#http-endpoints)
- [Policy Gates Integration](#policy-gates-integration)
- [Discord Webhook Notifications](#discord-webhook-notifications)
- [Full Working Example](#full-working-example)
- [Testing Your Agent](#testing-your-agent)

---

## AgentBase API Reference

`AgentBase` is the abstract foundation class in `agents/core/base.py`. All agents inherit from it.

### Constructor Parameters

```python
class AgentBase(ABC):
    def __init__(
        self,
        name: str,                    # Unique agent identifier (e.g., "director-01")
        role: str,                     # Agent role: director | executor | guardian | council
        tier: int = 4,                 # Tier number (default: 4)
        nats_url: str = "nats://localhost:10302",
        redis_url: str = "redis://localhost:10301/0",
        litellm_url: str = "http://localhost:10201",
        http_port: int = None,         # HTTP server port (auto-assigned if None)
        log_level: str = "INFO",
    ):
```

### Core Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `start` | `async start() -> None` | Initialize all connections and start the agent loop |
| `stop` | `async stop() -> None` | Graceful shutdown of all connections |
| `call_llm` | `async call_llm(prompt, model=None, temperature=0.7) -> str` | Send a prompt to the LLM |
| `publish` | `async publish(subject: str, message: dict) -> None` | Publish a message to NATS |
| `subscribe` | `async subscribe(subject: str, handler: Callable) -> None` | Subscribe to a NATS subject |
| `request` | `async request(subject: str, message: dict, timeout: float = 5.0) -> dict` | NATS request-reply pattern |
| `get_state` | `async get_state(key: str) -> Optional[dict]` | Retrieve state from Redis |
| `set_state` | `async set_state(key: str, value: dict, ttl: int = 3600) -> None` | Store state in Redis with TTL |
| `acquire_lock` | `async acquire_lock(name: str, timeout: float = 10.0) -> bool` | Distributed lock via Redis |
| `release_lock` | `async release_lock(name: str) -> None` | Release a distributed lock |
| `notify` | `async notify(message: str, level: str = "info") -> None` | Send Discord webhook notification |
| `record_metric` | `record_metric(name: str, value: float, labels: dict = None) -> None` | Record a Prometheus metric |

### Abstract Methods (Must Override)

| Method | Signature | Description |
|--------|-----------|-------------|
| `on_message` | `async on_message(subject: str, message: dict) -> None` | Handle incoming NATS messages |
| `on_health` | `async on_health() -> dict` | Return custom health check data |
| `on_cycle` | `async on_cycle() -> None` | Called every agent loop iteration |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Agent identifier |
| `role` | `str` | Agent role |
| `tier` | `int` | Tier number |
| `is_healthy` | `bool` | Health status |
| `uptime` | `float` | Seconds since start |
| `messages_processed` | `int` | Total messages handled |
| `last_error` | `Optional[Exception]` | Last error encountered |

---

## Creating a New Agent

### Step 1: Create Agent File

Create a new file at `agents/tiers/TIER-04/<role>/<agent-name>.py`:

```python
# agents/tiers/TIER-04/executor/my-executor.py

import asyncio
from agents.core.base import AgentBase

class MyExecutor(AgentBase):
    """Custom executor agent for specialized task processing."""

    def __init__(self, **kwargs):
        super().__init__(
            name="my-executor-01",
            role="executor",
            tier=4,
            **kwargs
        )
        self.processed_count = 0

    async def on_message(self, subject: str, message: dict) -> None:
        """Handle incoming task messages."""
        task_id = message.get("task_id", "unknown")
        self.logger.info(f"Processing task: {task_id}")

        # Process the task
        result = await self._process_task(message)

        # Publish result
        await self.publish(
            f"jart-os.04.task.executor.complete",
            {"task_id": task_id, "result": result}
        )
        self.processed_count += 1

    async def on_health(self) -> dict:
        """Return health status."""
        return {
            "processed_count": self.processed_count,
            "status": "healthy"
        }

    async def on_cycle(self) -> None:
        """Periodic maintenance."""
        self.logger.debug(f"Cycle tick — processed: {self.processed_count}")

    async def _process_task(self, message: dict) -> dict:
        """Core task processing logic."""
        prompt = message.get("payload", {}).get("prompt", "")

        # Call LLM for analysis
        response = await self.call_llm(
            prompt=prompt,
            model="glm-5",
            temperature=0.3
        )

        return {"analysis": response}


if __name__ == "__main__":
    agent = MyExecutor()
    asyncio.run(agent.start())
```

### Step 2: Create Dockerfile

```dockerfile
# agents/tiers/TIER-04/executor/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "-m", "my-executor"]
```

### Step 3: Create docker-compose.yml

```yaml
# agents/tiers/TIER-04/executor/docker-compose.yml
version: "3.8"

services:
  my-executor:
    build: .
    container_name: jart-os-my-executor
    environment:
      - NATS_URL=nats://jart-os-nats:10302
      - REDIS_URL=redis://jart-os-redis:10301/0
      - LITELLM_URL=http://jart-os-litellm:10201
      - AGENT_NAME=my-executor-01
      - AGENT_ROLE=executor
    networks:
      - jart-os-net
    ports:
      - "10401:10401"

networks:
  jart-os-net:
    external: true
```

### Step 4: Register NATS Subscriptions

```python
# In your agent's start method or on_cycle
await self.subscribe("jart-os.04.task.executor.*", self.on_message)
```

### Step 5: Test Locally

```bash
# Build and run
docker compose -f agents/tiers/TIER-04/executor/docker-compose.yml up --build

# Check logs
docker logs jart-os-my-executor -f
```

---

## Agent Lifecycle

Every agent follows the same lifecycle:

```
┌─────────┐    ┌───────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  INIT    │───▶│  CONNECT  │───▶│ SUBSCRIBE │───▶│   RUN    │───▶│ SHUTDOWN │
└─────────┘    └───────────┘    └───────────┘    └──────────┘    └──────────┘
  Load config    NATS, Redis      Register         on_cycle()      Cleanup
  Validate       LiteLLM          handlers         on_message()    Disconnect
  Setup logs     HTTP server                       loop forever
```

### Phase Details

1. **INIT** — Load configuration, validate environment, set up logging
2. **CONNECT** — Establish connections to NATS, Redis, LiteLLM; start HTTP server
3. **SUBSCRIBE** — Register NATS subject handlers based on agent role
4. **RUN** — Enter main loop; `on_cycle()` called each iteration; `on_message()` on inbound messages
5. **SHUTDOWN** — Graceful disconnect from all services; flush pending metrics

### NATS Subject Patterns by Role

| Role | Subscribe Pattern | Publish Pattern |
|------|-------------------|-----------------|
| Director | `jart-os.04.plan.director.*` | `jart-os.04.task.executor.dispatch` |
| Executor | `jart-os.04.task.executor.*` | `jart-os.04.task.executor.complete` |
| Guardian | `jart-os.04.review.guardian.*` | `jart-os.04.review.guardian.verdict` |
| Council | `jart-os.04.govern.council.*` | `jart-os.04.govern.council.decision` |

---

## NATS Messaging Patterns

### Publish (Fire and Forget)

```python
await self.publish(
    "jart-os.04.task.executor.dispatch",
    {
        "task_id": "task-001",
        "source": "director-01",
        "timestamp": "2025-01-15T10:00:00Z",
        "payload": {"action": "analyze", "data": "..."}
    }
)
```

### Request-Reply (Synchronous)

```python
# Send request and wait for response
response = await self.request(
    "jart-os.04.task.executor.run",
    {"task_id": "task-002", "payload": {"prompt": "Analyze this data"}},
    timeout=10.0  # seconds
)
print(response)  # {"status": "completed", "result": "..."}
```

### Subscribe (Event-Driven)

```python
# Subscribe to all executor events
await self.subscribe(
    "jart-os.04.task.executor.>",
    handler=self.on_message
)

# Subscribe to specific action
await self.subscribe(
    "jart-os.04.task.executor.dispatch",
    handler=self.handle_dispatch
)
```

### Wildcards

| Wildcard | Meaning | Example |
|----------|---------|---------|
| `*` | Single token | `jart-os.04.*.executor.run` |
| `>` | Multi-token (must be last) | `jart-os.04.task.executor.>` |

---

## Redis State Management

### Basic Operations

```python
# Store state
await self.set_state(
    "task:task-001:status",
    {"status": "processing", "started_at": "2025-01-15T10:00:00Z"},
    ttl=3600  # 1 hour TTL
)

# Retrieve state
state = await self.get_state("task:task-001:status")
# {"status": "processing", "started_at": "2025-01-15T10:00:00Z"}

# State returns None if key doesn't exist
missing = await self.get_state("nonexistent:key")
```

### Key Naming Convention

```
jart-os:{tier}:{domain}:{entity}:{id}:{attribute}
```

Examples:
- `jart-os:04:task:task-001:status`
- `jart-os:04:agent:director-01:state`
- `jart-os:04:session:abc123:context`

### Distributed Locks

```python
# Acquire lock (prevents concurrent access)
if await self.acquire_lock("task:task-001", timeout=30.0):
    try:
        # Critical section — only one agent at a time
        result = await self._process_exclusive()
    finally:
        await self.release_lock("task:task-001")
else:
    self.logger.warning("Could not acquire lock for task-001")
```

### Pub/Sub Channels

```python
# Publish to a channel
await self.redis.publish("jart-os:events:task", json.dumps({
    "event": "task.completed",
    "task_id": "task-001"
}))

# Subscribe to a channel (in on_cycle or separate task)
pubsub = self.redis.pubsub()
await pubsub.subscribe("jart-os:events:task")
async for message in pubsub.listen():
    if message["type"] == "message":
        data = json.loads(message["data"])
        await self._handle_event(data)
```

---

## LLM Calls via LiteLLM

### Basic Usage

```python
# Simple prompt
response = await self.call_llm(
    prompt="Explain the concept of recursion in simple terms.",
    model="glm-5",
    temperature=0.7
)
```

### Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| `glm-5` | Primary model, high quality | Complex reasoning, analysis |
| `glm-4.7` | Fast, efficient | Quick tasks, classification |
| `phi3-local` | Local model, no API needed | Offline, privacy-sensitive |

### Advanced Usage

```python
# Structured output with system prompt
response = await self.call_llm(
    prompt="Analyze this document for key themes.",
    model="glm-5",
    temperature=0.3  # Lower for more deterministic output
)

# Error handling
try:
    response = await self.call_llm(prompt="...", model="glm-5")
except ConnectionError:
    self.logger.error("LiteLLM unavailable — falling back")
    response = await self.call_llm(prompt="...", model="phi3-local")
except TimeoutError:
    self.logger.error("LLM call timed out")
    response = None
```

---

## HTTP Endpoints

Every agent exposes an HTTP server with standard endpoints:

### GET /health

```json
{
  "status": "healthy",
  "agent": "my-executor-01",
  "role": "executor",
  "tier": 4,
  "uptime_seconds": 3600,
  "custom": {
    "processed_count": 42
  }
}
```

### GET /metrics

Prometheus-format metrics:

```
# HELP jart_os_agent_tasks_total Total tasks processed
# TYPE jart_os_agent_tasks_total counter
jart_os_agent_tasks_total{agent="my-executor-01",role="executor"} 42

# HELP jart_os_agent_uptime_seconds Agent uptime in seconds
# TYPE jart_os_agent_uptime_seconds gauge
jart_os_agent_uptime_seconds{agent="my-executor-01"} 3600
```

### GET /state

```json
{
  "agent": "my-executor-01",
  "state": {
    "current_task": "task-042",
    "processed_count": 42,
    "last_error": null
  }
}
```

---

## Policy Gates Integration

Policy gates enforce quality and compliance at two checkpoints.

### Spec Gate (Pre-Execution)

Validates tasks before execution. Defined in `agents/policies/spec-gate.yaml`.

```python
# Before executing a task, validate against spec gate
validation = await self._check_spec_gate(task_spec)

if not validation["passed"]:
    self.logger.warning(f"Spec gate rejected: {validation['reasons']}")
    await self.notify(f"Task rejected by spec gate: {task_spec['task_id']}", "warning")
    return

# Proceed with execution
result = await self._execute(task_spec)
```

### Quality Gate (Post-Execution)

Validates results after execution. Defined in `agents/policies/quality-gate.yaml`.

```python
# After execution, validate result against quality gate
quality = await self._check_quality_gate(result)

if not quality["passed"]:
    self.logger.warning(f"Quality gate failed: {quality['reasons']}")
    # Route to guardian for review
    await self.publish(
        "jart-os.04.review.guardian.request",
        {"task_id": task_id, "result": result, "quality_report": quality}
    )
    return

# Result passes — publish completion
await self.publish("jart-os.04.task.executor.complete", result)
```

### Three Governance Aspects

| Aspect | Description | Validated By |
|--------|-------------|--------------|
| REGULATORY | Compliance with rules and standards | Guardian agent |
| PEDAGOGICAL | Educational quality and effectiveness | Council agent |
| TECHNICAL | Code quality, performance, correctness | Guardian agent |

---

## Discord Webhook Notifications

```python
# Send info notification
await self.notify("Task task-001 completed successfully")

# Send warning
await self.notify("Redis connection unstable — retrying", level="warning")

# Send error
await self.notify("Agent crashed: NullPointerException", level="error")

# Levels: info, warning, error, success
```

Configure the webhook URL in `.env`:

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK
```

---

## Full Working Example

```python
"""
Complete example agent demonstrating all Jart-OS features.
"""
import asyncio
import json
from datetime import datetime
from agents.core.base import AgentBase


class StudyAgent(AgentBase):
    """An agent that processes study material and generates summaries."""

    def __init__(self, **kwargs):
        super().__init__(
            name="study-agent-01",
            role="executor",
            tier=4,
            **kwargs
        )
        self.tasks_completed = 0
        self.tasks_failed = 0

    async def on_message(self, subject: str, message: dict) -> None:
        """Route messages based on action type."""
        task_id = message.get("task_id", "unknown")
        action = message.get("payload", {}).get("action", "unknown")

        self.logger.info(f"Received {action} for task {task_id}")

        try:
            if action == "summarize":
                await self._handle_summarize(task_id, message)
            elif action == "quiz":
                await self._handle_quiz(task_id, message)
            elif action == "review":
                await self._handle_review(task_id, message)
            else:
                self.logger.warning(f"Unknown action: {action}")
        except Exception as e:
            self.tasks_failed += 1
            self.logger.error(f"Task {task_id} failed: {e}")
            await self.notify(f"Task {task_id} failed: {e}", level="error")

    async def on_health(self) -> dict:
        return {
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "success_rate": (
                self.tasks_completed / (self.tasks_completed + self.tasks_failed)
                if (self.tasks_completed + self.tasks_failed) > 0
                else 0
            ),
        }

    async def on_cycle(self) -> None:
        """Periodic heartbeat."""
        self.logger.debug(
            f"Heartbeat — completed: {self.tasks_completed}, "
            f"failed: {self.tasks_failed}"
        )

    async def _handle_summarize(self, task_id: str, message: dict) -> None:
        """Generate a summary of study material."""
        content = message["payload"]["content"]

        # Acquire lock to prevent duplicate processing
        if not await self.acquire_lock(f"summarize:{task_id}", timeout=60.0):
            self.logger.warning(f"Lock busy for {task_id}")
            return

        try:
            # Call LLM
            summary = await self.call_llm(
                prompt=f"Summarize the following study material concisely:\n\n{content}",
                model="glm-5",
                temperature=0.3,
            )

            # Store result in Redis
            result = {
                "task_id": task_id,
                "summary": summary,
                "completed_at": datetime.utcnow().isoformat(),
            }
            await self.set_state(f"result:{task_id}", result, ttl=86400)

            # Check quality gate
            quality = await self._check_quality_gate(result)
            if quality["passed"]:
                await self.publish(
                    "jart-os.04.task.executor.complete",
                    {"task_id": task_id, "status": "completed", "result": result},
                )
                self.tasks_completed += 1
                await self.notify(f"Summary completed for {task_id}", level="success")
            else:
                await self.publish(
                    "jart-os.04.review.guardian.request",
                    {"task_id": task_id, "result": result, "quality": quality},
                )
        finally:
            await self.release_lock(f"summarize:{task_id}")

    async def _handle_quiz(self, task_id: str, message: dict) -> None:
        """Generate quiz questions from study material."""
        content = message["payload"]["content"]
        quiz = await self.call_llm(
            prompt=f"Generate 5 quiz questions from:\n\n{content}",
            model="glm-5",
            temperature=0.7,
        )
        await self.publish(
            "jart-os.04.task.executor.complete",
            {"task_id": task_id, "quiz": quiz},
        )
        self.tasks_completed += 1

    async def _handle_review(self, task_id: str, message: dict) -> None:
        """Review and validate existing content."""
        content = message["payload"]["content"]
        review = await self.call_llm(
            prompt=f"Review this content for accuracy and completeness:\n\n{content}",
            model="glm-5",
            temperature=0.2,
        )
        await self.publish(
            "jart-os.04.task.executor.complete",
            {"task_id": task_id, "review": review},
        )
        self.tasks_completed += 1


if __name__ == "__main__":
    agent = StudyAgent()
    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        asyncio.run(agent.stop())
```

---

## Testing Your Agent

### Unit Tests

```python
# tests/test_study_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from agents.tiers.TIER-04.executor.study_agent import StudyAgent


@pytest.fixture
def agent():
    return StudyAgent(
        nats_url="nats://mock:4222",
        redis_url="redis://mock:6379/0",
        litellm_url="http://mock:4000",
    )


@pytest.mark.asyncio
async def test_handle_summarize(agent):
    # Mock dependencies
    agent.call_llm = AsyncMock(return_value="Summary of content")
    agent.set_state = AsyncMock()
    agent.publish = AsyncMock()
    agent.acquire_lock = AsyncMock(return_value=True)
    agent.release_lock = AsyncMock()
    agent._check_quality_gate = AsyncMock(return_value={"passed": True})

    message = {
        "task_id": "test-001",
        "payload": {"action": "summarize", "content": "Long study text..."},
    }

    await agent.on_message("jart-os.04.task.executor.dispatch", message)

    agent.call_llm.assert_called_once()
    agent.publish.assert_called_once()
    assert agent.tasks_completed == 1
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
import docker


@pytest.fixture(scope="module")
def docker_env():
    """Start test Docker environment."""
    client = docker.from_env()
    # Start test containers
    # ...
    yield
    # Cleanup


@pytest.mark.asyncio
async def test_full_pipeline(docker_env):
    """Test complete task pipeline through NATS."""
    # Publish task
    # Wait for completion
    # Verify result in Redis
    pass
```

### Running Tests

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests (requires Docker)
pytest tests/integration/ -v

# All tests with coverage
pytest tests/ -v --cov=agents --cov-report=term-missing

# Specific test
pytest tests/test_study_agent.py::test_handle_summarize -v
```
