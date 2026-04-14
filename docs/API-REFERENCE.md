# API Reference

> Complete reference for all Jart-OS HTTP endpoints, messaging APIs, and data formats.

## Table of Contents

- [LiteLLM Proxy API](#litellm-proxy-api)
- [Redis API](#redis-api)
- [NATS API](#nats-api)
- [Agent HTTP API](#agent-http-api)
- [Prometheus Metrics](#prometheus-metrics)
- [Grafana](#grafana)
- [Mission Control](#mission-control)
- [Message Envelope Specification](#message-envelope-specification)
- [Error Response Format](#error-response-format)

---

## LiteLLM Proxy API

Base URL: `http://localhost:10201`

### POST /v1/chat/completions

Send a chat completion request to any configured model.

**Request:**

```json
{
  "model": "glm-5",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing in simple terms."}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "top_p": 1.0,
  "stream": false
}
```

**Response (200 OK):**

```json
{
  "id": "cmpl-abc123",
  "object": "chat.completion",
  "created": 1705312000,
  "model": "glm-5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Quantum computing uses quantum bits (qubits)..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  }
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | Yes | — | Model ID (see /v1/models) |
| `messages` | array | Yes | — | Array of message objects |
| `temperature` | float | No | 0.7 | Sampling temperature (0.0–2.0) |
| `max_tokens` | int | No | 2048 | Maximum tokens to generate |
| `top_p` | float | No | 1.0 | Nucleus sampling threshold |
| `stream` | bool | No | false | Enable streaming responses |

### GET /v1/models

List all available models.

**Response (200 OK):**

```json
{
  "object": "list",
  "data": [
    {
      "id": "glm-5",
      "object": "model",
      "owned_by": "zhipu"
    },
    {
      "id": "glm-4.7",
      "object": "model",
      "owned_by": "zhipu"
    },
    {
      "id": "phi3-local",
      "object": "model",
      "owned_by": "local"
    }
  ]
}
```

### GET /health

Health check endpoint.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "model_count": 3,
  "uptime_seconds": 86400
}
```

---

## Redis API

Connection: `redis://localhost:10301/0`

### Connection Parameters

| Parameter | Value |
|-----------|-------|
| Host | `localhost` (Docker: `jart-os-redis`) |
| Port | `10301` |
| Database | `0` |
| Password | (none by default) |

### Key Patterns

| Pattern | TTL | Description |
|---------|-----|-------------|
| `jart-os:{tier}:agent:{name}:state` | 3600s | Agent runtime state |
| `jart-os:{tier}:task:{id}:status` | 86400s | Task execution status |
| `jart-os:{tier}:task:{id}:result` | 86400s | Task execution result |
| `jart-os:{tier}:session:{id}:context` | 7200s | Session context data |
| `jart-os:{tier}:lock:{name}` | 30s | Distributed lock |

### Pub/Sub Channels

| Channel | Direction | Description |
|---------|-----------|-------------|
| `jart-os:events:task` | Agents → All | Task lifecycle events |
| `jart-os:events:agent` | Agent → Monitor | Agent status changes |
| `jart-os:events:governance` | Council → All | Governance decisions |
| `jart-os:alerts` | Any → Discord | Alert notifications |

### Example Commands

```bash
# Connect
docker exec -it jart-os-redis redis-cli -p 10301

# Get agent state
GET "jart-os:04:agent:director-01:state"

# Set task status
SET "jart-os:04:task:task-001:status" '{"status":"processing"}' EX 86400

# Publish event
PUBLISH "jart-os:events:task" '{"event":"task.started","task_id":"task-001"}'

# List all Jart-OS keys
KEYS jart-os:*

# Monitor all commands (debugging)
MONITOR
```

---

## NATS API

Server: `nats://localhost:10302`

### Connection Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 10302 | NATS | Client connections |
| 10303 | NATS | Cluster routes |
| 10304 | NATS | JetStream / monitoring |

### Subject Schema

```
jart-os.{tier}.{domain}.{role}.{action}
```

| Component | Values | Description |
|-----------|--------|-------------|
| `tier` | 01–10 | Tier number |
| `domain` | plan, task, review, govern, system | Functional domain |
| `role` | director, executor, guardian, council | Agent role |
| `action` | dispatch, complete, request, verdict, decision | Specific action |

### Standard Subjects

| Subject | Publisher | Subscriber | Purpose |
|---------|-----------|------------|---------|
| `jart-os.04.plan.director.dispatch` | Director | Executors | Task assignment |
| `jart-os.04.task.executor.complete` | Executor | Director | Task completion |
| `jart-os.04.review.guardian.request` | Any | Guardian | Quality review request |
| `jart-os.04.review.guardian.verdict` | Guardian | Requester | Review result |
| `jart-os.04.govern.council.proposal` | Director | Council | Governance proposal |
| `jart-os.04.govern.council.decision` | Council | All | Final governance decision |
| `jart-os.04.system.*.heartbeat` | All | Monitor | Agent heartbeat |

### JetStream Configuration

```bash
# Check JetStream status
curl http://localhost:10302/jsz

# Stream information
curl http://localhost:10302/jsz?streams=true

# Consumer information
curl http://localhost:10302/jsz?consumers=true
```

---

## Agent HTTP API

Every agent exposes an HTTP server for monitoring and management.

### GET /health

Returns agent health status.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "agent": "executor-01",
  "role": "executor",
  "tier": 4,
  "uptime_seconds": 3600,
  "nats_connected": true,
  "redis_connected": true,
  "litellm_reachable": true,
  "custom": {
    "tasks_completed": 42,
    "tasks_failed": 1
  }
}
```

**Response (503 Service Unavailable):**

```json
{
  "status": "unhealthy",
  "agent": "executor-01",
  "issues": [
    "NATS disconnected",
    "Redis connection timeout"
  ]
}
```

### GET /metrics

Returns Prometheus-format metrics.

**Response (200 OK):**

```
# HELP jart_os_agent_tasks_total Total tasks processed by this agent
# TYPE jart_os_agent_tasks_total counter
jart_os_agent_tasks_total{agent="executor-01",role="executor",tier="4"} 42

# HELP jart_os_agent_tasks_failed_total Total failed tasks
# TYPE jart_os_agent_tasks_failed_total counter
jart_os_agent_tasks_failed_total{agent="executor-01",role="executor"} 1

# HELP jart_os_agent_uptime_seconds Agent uptime in seconds
# TYPE jart_os_agent_uptime_seconds gauge
jart_os_agent_uptime_seconds{agent="executor-01"} 3600

# HELP jart_os_agent_llm_calls_total Total LLM API calls
# TYPE jart_os_agent_llm_calls_total counter
jart_os_agent_llm_calls_total{agent="executor-01",model="glm-5"} 38

# HELP jart_os_agent_nats_messages_total Total NATS messages processed
# TYPE jart_os_agent_nats_messages_total counter
jart_os_agent_nats_messages_total{agent="executor-01",direction="inbound"} 50
```

### GET /state

Returns current agent state from Redis.

**Response (200 OK):**

```json
{
  "agent": "executor-01",
  "role": "executor",
  "tier": 4,
  "state": {
    "current_task": "task-042",
    "tasks_completed": 42,
    "last_error": null,
    "last_heartbeat": "2025-01-15T10:30:00Z"
  },
  "config": {
    "model": "glm-5",
    "temperature": 0.3,
    "max_retries": 3
  }
}
```

---

## Prometheus Metrics

Server: `http://localhost:10901`

### Access

- **UI**: http://localhost:10901
- **API**: http://localhost:10901/api/v1/

### Metric Names

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `jart_os_agent_tasks_total` | counter | agent, role, tier | Total tasks processed |
| `jart_os_agent_tasks_failed_total` | counter | agent, role | Total failed tasks |
| `jart_os_agent_uptime_seconds` | gauge | agent | Agent uptime |
| `jart_os_agent_llm_calls_total` | counter | agent, model | LLM API calls |
| `jart_os_agent_llm_latency_seconds` | histogram | agent, model | LLM response latency |
| `jart_os_agent_nats_messages_total` | counter | agent, direction | NATS message count |
| `jart_os_agent_redis_operations_total` | counter | agent, operation | Redis operations |
| `jart_os_agent_http_requests_total` | counter | agent, method, path | HTTP requests |
| `jart_os_system_health` | gauge | service | Service health (1=up, 0=down) |

### Useful PromQL Queries

```promql
# Task success rate
rate(jart_os_agent_tasks_total[5m]) / rate(jart_os_agent_tasks_failed_total[5m])

# Average LLM latency
rate(jart_os_agent_llm_latency_seconds_sum[5m]) / rate(jart_os_agent_llm_latency_seconds_count[5m])

# Messages per second by agent
sum(rate(jart_os_agent_nats_messages_total{direction="inbound"}[5m])) by (agent)

# Service availability
jart_os_system_health
```

---

## Grafana

Access: `http://localhost:10702`

### Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |

> **Change the default password on first login.**

### Data Source Configuration

Grafana is pre-configured with Prometheus as a data source:

| Setting | Value |
|---------|-------|
| Type | Prometheus |
| URL | `http://jart-os-prometheus:9090` |
| Access | Server (proxy) |
| Scrape interval | 15s |

### Dashboard Setup

1. Navigate to Dashboards → Import
2. Upload a JSON dashboard or paste a Grafana.com ID
3. Select the Prometheus data source
4. Click Import

---

## Mission Control

Access: `http://localhost:10701`

### Current State

Mission Control is currently a **mockup dashboard** running on `nginx:alpine`. It serves static HTML/CSS/JS for visual prototyping.

### Planned Features

- Real-time agent status grid
- Task pipeline visualization
- Governance decision feed
- Alert management
- System resource monitoring

### Architecture

```yaml
# Current mockup
services:
  mission-control:
    image: nginx:alpine
    container_name: jart-os-mission-control
    ports:
      - "10701:80"
    networks:
      - jart-os-net
```

---

## Message Envelope Specification

All messages in NATS and Redis pub/sub follow a standard envelope format.

### Standard Envelope

```json
{
  "task_id": "task-001",
  "source": "director-01",
  "target": "executor-01",
  "timestamp": "2025-01-15T10:00:00.000Z",
  "correlation_id": "corr-abc123",
  "reply_to": "jart-os.04.task.executor.complete",
  "priority": "normal",
  "ttl_seconds": 300,
  "payload": {
    "action": "analyze",
    "data": "..."
  },
  "metadata": {
    "retry_count": 0,
    "parent_task_id": null,
    "governance_aspect": null
  }
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Unique task identifier |
| `source` | string | Yes | Originating agent name |
| `target` | string | No | Target agent (omit for broadcast) |
| `timestamp` | ISO 8601 | Yes | Message creation time |
| `correlation_id` | string | No | For request-reply correlation |
| `reply_to` | string | No | NATS reply subject |
| `priority` | enum | No | `low`, `normal`, `high`, `critical` (default: `normal`) |
| `ttl_seconds` | int | No | Time-to-live for processing (default: 300) |
| `payload` | object | Yes | Task-specific data |
| `metadata` | object | No | Additional context |

### Governance Envelope Extension

For governance-related messages:

```json
{
  "task_id": "gov-001",
  "source": "director-01",
  "timestamp": "2025-01-15T10:00:00.000Z",
  "payload": {
    "aspect": "REGULATORY",
    "proposal": "Validate task output against quality standards",
    "evidence": {...}
  },
  "metadata": {
    "governance_aspect": "REGULATORY",
    "voting_required": true,
    "quorum": 2
  }
}
```

---

## Error Response Format

All APIs return errors in a consistent format.

### HTTP Error Response

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task 'task-999' does not exist",
    "details": {
      "task_id": "task-999",
      "suggestion": "Check the task ID or list active tasks"
    },
    "timestamp": "2025-01-15T10:00:00.000Z"
  }
}
```

### Standard Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request body |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `TIMEOUT` | 408 | Request timed out |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependent service down |
| `GATEWAY_TIMEOUT` | 504 | Upstream service timeout |

### NATS Error Message

```json
{
  "task_id": "task-001",
  "error": true,
  "error_code": "EXECUTION_FAILED",
  "error_message": "LLM call timed out after 30 seconds",
  "retry_eligible": true,
  "timestamp": "2025-01-15T10:00:00.000Z"
}
```
