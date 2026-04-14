# Testing Guide

> Test-Driven Development strategy, test pyramid, and CI/CD integration for Jart-OS.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Pyramid](#test-pyramid)
- [Running Tests](#running-tests)
- [Unit Testing Agents](#unit-testing-agents)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Policy Gate Testing](#policy-gate-testing)
- [Test Fixtures and Factories](#test-fixtures-and-factories)
- [Coverage Requirements](#coverage-requirements)
- [CI/CD Integration](#cicd-integration)
- [Writing Testable Specs](#writing-testable-specs)

---

## Testing Philosophy

Jart-OS follows a **spec-driven, test-first** approach:

1. **Write the spec** — Define what the system should do (given/when/then)
2. **Write the test** — Express the spec as an automated test (RED)
3. **Write the code** — Implement the minimum to pass (GREEN)
4. **Refactor** — Clean up while keeping tests green (REFACTOR)

### Principles

- **Every feature starts with a failing test** — No code without a test
- **Tests are documentation** — A new developer should understand the system by reading tests
- **Fast feedback loop** — Unit tests run in milliseconds, integration tests in seconds
- **Deterministic** — Same test, same result, every time (no flaky tests)
- **Isolated** — Tests don't depend on each other or external state

---

## Test Pyramid

```
         ╱╲
        ╱  ╲          E2E Tests (few, slow, expensive)
       ╱    ╲         test_e2e.py — full pipeline validation
      ╱──────╲
     ╱        ╲       Integration Tests (moderate)
    ╱          ╲      Docker Compose environment, real services
   ╱────────────╲
  ╱              ╲    Unit Tests (many, fast, cheap)
 ╱                ╲   Mocked dependencies, pure logic
╱──────────────────╲
```

| Level | Count | Speed | Scope | Dependencies |
|-------|-------|-------|-------|--------------|
| **Unit** | Many (100+) | < 100ms | Single function/class | Mocked |
| **Integration** | Moderate (20-50) | 1-10s | Service interaction | Real Docker |
| **E2E** | Few (5-10) | 30s-5min | Full pipeline | Full stack |

### Distribution Target

- **70%** Unit tests
- **20%** Integration tests
- **10%** E2E tests

---

## Running Tests

### Prerequisites

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Commands

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run only e2e tests
pytest tests/test_e2e.py -v

# Run a specific test file
pytest tests/unit/test_agent_base.py -v

# Run a specific test function
pytest tests/unit/test_agent_base.py::test_agent_init -v

# Run tests matching a pattern
pytest tests/ -v -k "nats"

# Run with coverage report
pytest tests/ -v --cov=agents --cov-report=term-missing

# Run with HTML coverage report
pytest tests/ -v --cov=agents --cov-report=html
open htmlcov/index.html

# Run with verbose output and no capture
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run tests in parallel (faster)
pip install pytest-xdist
pytest tests/ -v -n auto
```

### Test Discovery

```
tests/
├── unit/
│   ├── test_agent_base.py
│   ├── test_director.py
│   ├── test_executor.py
│   ├── test_guardian.py
│   └── test_council.py
├── integration/
│   ├── test_nats_messaging.py
│   ├── test_redis_state.py
│   └── test_litellm_proxy.py
├── e2e/
│   └── test_pipeline.py
├── conftest.py              # Shared fixtures
└── test_e2e.py              # Legacy e2e test
```

---

## Unit Testing Agents

### Mocking Strategy

Unit tests mock all external dependencies: NATS, Redis, LiteLLM, HTTP.

```python
# tests/unit/test_executor.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestExecutorAgent:
    """Unit tests for the Executor agent."""

    @pytest.fixture
    def executor(self):
        """Create an Executor instance with mocked dependencies."""
        with patch("agents.core.base.nats") as mock_nats, \
             patch("agents.core.base.redis") as mock_redis:

            agent = Executor(
                name="executor-test-01",
                role="executor",
                tier=4,
                nats_url="nats://mock:4222",
                redis_url="redis://mock:6379/0",
                litellm_url="http://mock:4000",
            )

            # Mock async methods
            agent.call_llm = AsyncMock(return_value="LLM response")
            agent.publish = AsyncMock()
            agent.subscribe = AsyncMock()
            agent.get_state = AsyncMock(return_value=None)
            agent.set_state = AsyncMock()
            agent.acquire_lock = AsyncMock(return_value=True)
            agent.release_lock = AsyncMock()
            agent.notify = AsyncMock()

            return agent

    @pytest.mark.asyncio
    async def test_process_task_success(self, executor):
        """Test successful task processing."""
        message = {
            "task_id": "task-001",
            "source": "director-01",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "action": "analyze",
                "prompt": "Analyze this data",
            },
        }

        await executor.on_message(
            "jart-os.04.task.executor.dispatch", message
        )

        # Verify LLM was called
        executor.call_llm.assert_called_once_with(
            prompt="Analyze this data",
            model="glm-5",
            temperature=0.3,
        )

        # Verify result was published
        executor.publish.assert_called_once()
        call_args = executor.publish.call_args
        assert "task-001" in str(call_args)

    @pytest.mark.asyncio
    async def test_process_task_llm_failure(self, executor):
        """Test handling of LLM call failure."""
        executor.call_llm = AsyncMock(side_effect=TimeoutError("LLM timeout"))

        message = {
            "task_id": "task-002",
            "payload": {"action": "analyze", "prompt": "test"},
        }

        # Should not raise — error should be handled gracefully
        await executor.on_message("jart-os.04.task.executor.dispatch", message)

        # Verify error notification was sent
        executor.notify.assert_called()
        assert "error" in str(executor.notify.call_args).lower()

    @pytest.mark.asyncio
    async def test_lock_contention(self, executor):
        """Test behavior when lock cannot be acquired."""
        executor.acquire_lock = AsyncMock(return_value=False)

        message = {
            "task_id": "task-003",
            "payload": {"action": "analyze", "prompt": "test"},
        }

        await executor.on_message("jart-os.04.task.executor.dispatch", message)

        # Should NOT call LLM if lock not acquired
        executor.call_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_health_check(self, executor):
        """Test health endpoint returns correct data."""
        executor.tasks_completed = 42
        executor.tasks_failed = 2

        health = await executor.on_health()

        assert health["tasks_completed"] == 42
        assert health["tasks_failed"] == 2
        assert health["status"] == "healthy"
```

### Mocking NATS

```python
from unittest.mock import AsyncMock

# Mock NATS publish
agent.publish = AsyncMock()

# Verify the call
agent.publish.assert_called_once_with(
    "jart-os.04.task.executor.complete",
    {"task_id": "task-001", "status": "completed"}
)

# Mock NATS request-reply
agent.request = AsyncMock(return_value={"status": "approved"})

result = await agent.request("jart-os.04.govern.council.proposal", {})
assert result["status"] == "approved"
```

### Mocking Redis

```python
# Mock Redis get_state
agent.get_state = AsyncMock(return_value={"status": "processing"})

# Mock Redis set_state
agent.set_state = AsyncMock()

# Verify state was stored
agent.set_state.assert_called_with(
    "task:task-001:status",
    {"status": "completed"},
    ttl=86400
)
```

### Mocking LLM

```python
# Mock successful LLM call
agent.call_llm = AsyncMock(return_value="Generated summary...")

# Mock LLM timeout
agent.call_llm = AsyncMock(side_effect=TimeoutError("LLM timeout"))

# Mock LLM returning structured data
agent.call_llm = AsyncMock(return_value=json.dumps({
    "summary": "...",
    "key_points": ["point1", "point2"]
}))
```

---

## Integration Testing

Integration tests use real Docker services (Redis, NATS, LiteLLM) but mock external APIs.

### Setup

```python
# tests/integration/conftest.py
import pytest
import asyncio
import docker


@pytest.fixture(scope="module")
def docker_services():
    """Start Docker Compose test environment."""
    client = docker.from_env()

    # Start test infrastructure
    client.containers.run(
        "redis:7-alpine",
        name="jart-os-test-redis",
        ports={"6379/tcp": 10301},
        detach=True,
        remove=True,
    )

    client.containers.run(
        "nats:2-alpine",
        name="jart-os-test-nats",
        ports={"4222/tcp": 10302},
        command="--jetstream",
        detach=True,
        remove=True,
    )

    yield

    # Cleanup
    for container in client.containers.list():
        if "jart-os-test" in container.name:
            container.stop()


@pytest.fixture
async def redis_client():
    """Async Redis client for testing."""
    import aioredis
    client = await aioredis.from_url("redis://localhost:10301/0")
    yield client
    await client.flushdb()
    await client.close()
```

### Example Integration Test

```python
# tests/integration/test_redis_state.py
import pytest


@pytest.mark.asyncio
async def test_agent_state_round_trip(redis_client):
    """Test that agent state can be stored and retrieved."""
    from agents.core.base import AgentBase

    agent = MyTestAgent(redis_url="redis://localhost:10301/0")
    await agent._connect_redis()

    # Store state
    await agent.set_state("test:key", {"value": "hello"}, ttl=60)

    # Retrieve state
    result = await agent.get_state("test:key")

    assert result == {"value": "hello"}
```

---

## End-to-End Testing

### test_e2e.py Walkthrough

The E2E test validates the complete pipeline: Director → Executor → Guardian → Council.

```python
# tests/test_e2e.py
"""
End-to-end test for the full Jart-OS pipeline.

Prerequisites:
- All Docker services running (./scripts/boot.sh start)
- LiteLLM configured with at least one model

Usage:
    pytest tests/test_e2e.py -v -s
"""
import pytest
import asyncio
import httpx
import json


BASE_URLS = {
    "litellm": "http://localhost:10201",
    "redis": "redis://localhost:10301/0",
    "nats": "nats://localhost:10302",
    "mission_control": "http://localhost:10701",
    "grafana": "http://localhost:10702",
    "prometheus": "http://localhost:10901",
}


@pytest.mark.asyncio
async def test_all_services_healthy():
    """Verify all infrastructure services are running."""
    async with httpx.AsyncClient() as client:
        # LiteLLM
        resp = await client.get(f"{BASE_URLS['litellm']}/health")
        assert resp.status_code == 200

        # Prometheus
        resp = await client.get(f"{BASE_URLS['prometheus']}/api/v1/targets")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_llm_completion():
    """Test LLM completion through LiteLLM proxy."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URLS['litellm']}/v1/chat/completions",
            json={
                "model": "glm-5",
                "messages": [{"role": "user", "content": "Say hello"}],
                "max_tokens": 50,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) > 0


@pytest.mark.asyncio
async def test_full_task_pipeline():
    """Test complete task lifecycle: dispatch → execute → review → approve."""
    # This test sends a task through the full agent pipeline
    # and verifies the result at each stage
    pass
```

---

## Policy Gate Testing

### Spec Gate Tests

```python
# tests/unit/test_spec_gate.py
import pytest
import yaml


@pytest.fixture
def spec_gate_config():
    """Load spec gate configuration."""
    with open("agents/policies/spec-gate.yaml") as f:
        return yaml.safe_load(f)


def test_spec_gate_rejects_empty_task(spec_gate_config):
    """Spec gate should reject tasks without required fields."""
    task = {}
    result = validate_spec_gate(task, spec_gate_config)
    assert result["passed"] is False
    assert "task_id" in str(result["reasons"])


def test_spec_gate_rejects_missing_payload(spec_gate_config):
    """Spec gate should reject tasks without payload."""
    task = {"task_id": "task-001", "source": "director-01"}
    result = validate_spec_gate(task, spec_gate_config)
    assert result["passed"] is False


def test_spec_gate_accepts_valid_task(spec_gate_config):
    """Spec gate should accept well-formed tasks."""
    task = {
        "task_id": "task-001",
        "source": "director-01",
        "timestamp": "2025-01-15T10:00:00Z",
        "payload": {"action": "analyze", "prompt": "Test prompt"},
    }
    result = validate_spec_gate(task, spec_gate_config)
    assert result["passed"] is True
```

### Quality Gate Tests

```python
# tests/unit/test_quality_gate.py
import pytest


def test_quality_gate_rejects_empty_result():
    """Quality gate should reject empty results."""
    result = {"task_id": "task-001", "output": ""}
    quality = validate_quality_gate(result)
    assert quality["passed"] is False


def test_quality_gate_rejects_low_confidence():
    """Quality gate should reject results below confidence threshold."""
    result = {"task_id": "task-001", "output": "Some output", "confidence": 0.3}
    quality = validate_quality_gate(result)
    assert quality["passed"] is False


def test_quality_gate_accepts_high_quality():
    """Quality gate should accept high-quality results."""
    result = {
        "task_id": "task-001",
        "output": "Comprehensive analysis...",
        "confidence": 0.9,
        "completeness": 0.85,
    }
    quality = validate_quality_gate(result)
    assert quality["passed"] is True
```

---

## Test Fixtures and Factories

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock
from datetime import datetime


@pytest.fixture
def sample_message():
    """Standard message envelope for testing."""
    return {
        "task_id": "test-task-001",
        "source": "director-test",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "action": "analyze",
            "prompt": "Test prompt for analysis",
        },
    }


@pytest.fixture
def mock_agent():
    """Agent with all dependencies mocked."""
    agent = MockAgent(name="test-agent", role="executor", tier=4)
    agent.call_llm = AsyncMock(return_value="mock response")
    agent.publish = AsyncMock()
    agent.subscribe = AsyncMock()
    agent.get_state = AsyncMock(return_value=None)
    agent.set_state = AsyncMock()
    agent.acquire_lock = AsyncMock(return_value=True)
    agent.release_lock = AsyncMock()
    agent.notify = AsyncMock()
    return agent


@pytest.fixture
def governance_message():
    """Message with governance metadata."""
    return {
        "task_id": "gov-test-001",
        "source": "director-test",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "aspect": "REGULATORY",
            "proposal": "Validate output quality",
        },
        "metadata": {
            "governance_aspect": "REGULATORY",
            "voting_required": True,
        },
    }
```

### Test Data Factory

```python
# tests/factories.py
from datetime import datetime
import uuid


def make_message(**overrides):
    """Create a test message with sensible defaults."""
    defaults = {
        "task_id": f"task-{uuid.uuid4().hex[:8]}",
        "source": "director-test",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {"action": "analyze", "prompt": "Test prompt"},
    }
    defaults.update(overrides)
    return defaults


def make_governance_message(aspect="REGULATORY", **overrides):
    """Create a governance test message."""
    return make_message(
        payload={
            "aspect": aspect,
            "proposal": "Test governance proposal",
        },
        metadata={
            "governance_aspect": aspect,
            "voting_required": True,
        },
        **overrides,
    )
```

---

## Coverage Requirements

### Minimum Thresholds

| Module | Minimum Coverage | Current |
|--------|-----------------|---------|
| `agents/core/` | 90% | — |
| `agents/runtime/` | 80% | — |
| `agents/tiers/` | 75% | — |
| `agents/policies/` | 85% | — |
| **Overall** | **80%** | — |

### Running Coverage

```bash
# Terminal report with missing lines
pytest tests/ --cov=agents --cov-report=term-missing

# HTML report (detailed line-by-line)
pytest tests/ --cov=agents --cov-report=html
open htmlcov/index.html

# Fail if below threshold
pytest tests/ --cov=agents --cov-fail-under=80
```

### Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["agents"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__",
    "pass",
    "raise NotImplementedError",
]
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check agents/ tests/
      - run: ruff format --check agents/ tests/

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt pytest pytest-asyncio pytest-cov
      - run: pytest tests/unit/ -v --cov=agents --cov-fail-under=80

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Start Docker services
        run: |
          docker compose -f services/TIER-01/docker-compose.yml up -d
          docker compose -f services/TIER-03/docker-compose.yml up -d
          sleep 10
      - run: pip install -r requirements.txt pytest pytest-asyncio
      - run: pytest tests/integration/ -v
      - name: Stop Docker services
        if: always()
        run: docker compose down

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Start all services
        run: |
          docker compose up -d
          sleep 15
      - run: pip install -r requirements.txt pytest pytest-asyncio httpx
      - run: pytest tests/test_e2e.py -v
      - name: Stop all services
        if: always()
        run: docker compose down
```

---

## Writing Testable Specs

### Given/When/Then Format

Write specifications in a structured format before coding:

```gherkin
Feature: Task Execution

  Scenario: Successful task processing
    Given an executor agent is running
    And a valid task message is received
    When the agent processes the task
    Then the LLM should be called with the correct prompt
    And the result should be published to NATS
    And the task count should increment

  Scenario: LLM timeout handling
    Given an executor agent is running
    And the LLM service is unavailable
    When the agent attempts to process a task
    Then the error should be logged
    And a Discord notification should be sent
    And the task should be marked as failed

  Scenario: Lock contention
    Given an executor agent is running
    And another agent holds the lock for the task
    When the agent attempts to process the same task
    Then the agent should skip processing
    And no duplicate work should occur
```

### Converting Specs to Tests

```python
# From the spec above:
@pytest.mark.asyncio
async def test_successful_task_processing(mock_agent, sample_message):
    """Given an executor agent is running and a valid task message is received,
    When the agent processes the task,
    Then the LLM should be called and result published."""
    # When
    await mock_agent.on_message("jart-os.04.task.executor.dispatch", sample_message)

    # Then
    mock_agent.call_llm.assert_called_once()
    mock_agent.publish.assert_called_once()
    assert mock_agent.tasks_completed == 1
```
