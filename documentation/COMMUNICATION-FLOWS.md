# Communication Flows
# Jart-OS NATS Messaging — Complete Reference

**Version:** 1.0.0
**Date:** 2026-04-16
**Status:** CANONICAL for all inter-service messaging
**Source:** Distilled from CANONICAL-SPEC §12 + Agent Protocol + OPENCLAW-system

---

## Table of Contents

1. [Overview](#1-overview)
2. [NATS Subject Taxonomy](#2-nats-subject-taxonomy)
3. [Message Envelope](#3-message-envelope)
4. [Agent Communication Flows](#4-agent-communication-flows)
5. [Pipeline Communication Flows](#5-pipeline-communication-flows)
6. [Infrastructure Flows](#6-infrastructure-flows)
7. [External Integration Flows](#7-external-integration-flows)
8. [Error Handling & Retries](#8-error-handling--retries)
9. [Redis State Patterns](#9-redis-state-patterns)
10. [Monitoring & Observability](#10-monitoring--observability)

---

## 1. Overview

### Communication Backbone: NATS JetStream

**ALL inter-component messaging goes through NATS.** No exceptions.

| Component | Role |
|-----------|------|
| **NATS JetStream** | Persistent messaging, request/reply, wildcards |
| **Redis** | State, cache, locks, rate-limiting (NOT messaging) |
| **LiteLLM** | LLM proxy (agents call LLMs through this, not NATS) |

### Why NATS (not Redis PubSub)

| Feature | Redis PubSub | NATS JetStream |
|---------|-------------|-----------------|
| Persistence | No (fire & forget) | Yes (replay, durable) |
| Request/Reply | Manual | Built-in |
| Wildcards | No | Yes (`>`, `*`) |
| Backpressure | No | Yes (flow control) |
| Monitoring | Manual | Built-in dashboard (:10304) |
| At-least-once | No | Yes |

---

## 2. NATS Subject Taxonomy

### Format

```
jart-os.<tier>.<domain>.<role>.<action>
```

### Components

| Part | Values | Description |
|------|--------|-------------|
| `tier` | 02, 03, 04, 05, 06, 07, 09 | Service tier |
| `domain` | study, dev, infra, pipeline, system | Functional domain |
| `role` | director, executor, guardian, council, pipeline, system | Agent/process role |
| `action` | command, event, query, verdict, vote, proposal, check, status | Action type |

### Complete Subject Map

```
# TIER-02: GATEWAY
jart-os.02.gateway.litellm.status
jart-os.02.gateway.openclaw.command
jart-os.02.gateway.openclaw.events

# TIER-03: SERVICES (internal events)
jart-os.03.services.redis.status
jart-os.03.services.nats.status

# TIER-04: AGENTS — Study Domain
jart-os.04.study.director.command       # External task requests
jart-os.04.study.director.events        # Director state changes
jart-os.04.study.director.status        # Health/status queries
jart-os.04.study.executor.command       # Sub-task assignments
jart-os.04.study.executor.events        # Execution progress
jart-os.04.study.guardian.checks        # Validation requests
jart-os.04.study.guardian.verdicts      # Pass/fail verdicts
jart-os.04.study.council.proposals      # Consensus proposals
jart-os.04.study.council.votes          # Individual votes
jart-os.04.study.council.decisions      # Final decisions

# TIER-04: AGENTS — Dev Domain (future)
jart-os.04.dev.director.command
jart-os.04.dev.executor.command
jart-os.04.dev.guardian.checks

# TIER-05: FRAMEWORKS
jart-os.05.study-domain.command
jart-os.05.study-domain.events

# TIER-06: PIPELINES
jart-os.06.pipeline.pdf.command         # Start PDF processing
jart-os.06.pipeline.pdf.events          # PDF progress events
jart-os.06.pipeline.photos.command      # Start photo processing
jart-os.06.pipeline.photos.events       # Photo progress events
jart-os.06.pipeline.video.command       # Start video processing
jart-os.06.pipeline.video.events        # Video progress events
jart-os.06.pipeline.rag.command         # Start RAG indexing
jart-os.06.pipeline.rag.query           # Query RAG store
jart-os.06.pipeline.rag.events          # RAG indexing events

# TIER-07: INTERFACES
jart-os.07.ui.mission-control.command
jart-os.07.ui.grafana.query

# TIER-09: CONTROL
jart-os.09.control.metrics.collect
jart-os.09.control.alerts.trigger

# SYSTEM-WIDE
jart-os.system.broadcast                # System-wide announcements
jart-os.system.health                   # Health check requests
```

### Wildcard Patterns

```
jart-os.04.>                     # All agent messages
jart-os.04.study.>               # All study domain agent messages
jart-os.06.pipeline.>            # All pipeline messages
jart-os.*.director.command       # All director commands across domains
jart-os.>                        # Everything (monitoring/debug)
```

---

## 3. Message Envelope

### Standard Envelope (All Messages)

```json
{
  "task_id": "OP2-2026-TEM3-001",
  "from": "director-study",
  "to": "executor-study",
  "timestamp": "2026-04-16T12:00:00Z",
  "priority": "normal",
  "retry_count": 0,
  "max_retries": 3,
  "timeout_seconds": 120,
  "payload": {
    "objective": "Generate summary for topic 3",
    "spec": {},
    "success_criteria": [],
    "model_hint": "glm-4.7",
    "context": {}
  }
}
```

### Priority Levels

| Level | Use Case | Timeout |
|-------|----------|---------|
| `critical` | Exam answers, legal compliance | 300s |
| `high` | Active study sessions | 120s |
| `normal` | Content generation, pipelines | 120s |
| `low` | Background indexing, cleanup | 300s |

### Verdict Envelope (Guardian → Director)

```json
{
  "task_id": "OP2-2026-TEM3-001",
  "from": "guardian",
  "to": "director-study",
  "timestamp": "2026-04-16T12:05:00Z",
  "verdict": "PASS",
  "score": {
    "completeness": 0.92,
    "accuracy": 0.95,
    "format": 1.0
  },
  "feedback": "",
  "payload": {
    "validated_content": "..."
  }
}
```

### Council Vote Envelope

```json
{
  "task_id": "OP2-2026-TEM3-001",
  "proposal_id": "COUNCIL-2026-001",
  "from": "council-legal",
  "to": "council",
  "timestamp": "2026-04-16T12:10:00Z",
  "vote": "PASS",
  "domain": "legal",
  "rationale": "All regulations referenced correctly"
}
```

### Pipeline Event Envelope

```json
{
  "task_id": "PIPE-PDF-2026-001",
  "from": "pipe-pdf",
  "to": "pipe-rag",
  "timestamp": "2026-04-16T12:00:00Z",
  "pipeline": "pdf",
  "stage": "extraction_complete",
  "progress": {
    "total": 872,
    "processed": 50,
    "failed": 2,
    "percent": 5.7
  },
  "output": {
    "chunks_generated": 1250,
    "output_path": "/data/processed/pdfs/chunks/"
  }
}
```

---

## 4. Agent Communication Flows

### Flow 1: Task Lifecycle (Standard)

```
USER/OPENCODE → NATS: jart-os.04.study.director.command
    │
    ▼
DIRECTOR receives task
    ├── Parses objective
    ├── Queries RAG (via pipe-rag)
    ├── Plans sub-tasks
    │
    ├──► NATS: jart-os.04.study.executor.command (sub-task 1)
    │        │
    │        ▼
    │    EXECUTOR generates content
    │        │
    │        ├──► NATS: jart-os.04.study.guardian.checks
    │        │        │
    │        │        ▼
    │        │    GUARDIAN validates
    │        │        │
    │        │        ├──► NATS: jart-os.04.study.guardian.verdicts (PASS)
    │        │        │    → EXECUTOR sends result to DIRECTOR
    │        │        │
    │        │        └──► NATS: jart-os.04.study.guardian.verdicts (FAIL)
    │        │             → EXECUTOR retries with feedback (max 3)
    │        │
    │        └──► NATS: jart-os.04.study.director.events (sub-task 1 done)
    │
    ├──► NATS: jart-os.04.study.executor.command (sub-task 2)
    │    ... same flow ...
    │
    └──► All sub-tasks complete
         DIRECTOR assembles final result
         NATS: jart-os.04.study.director.events (task complete)
```

### Flow 2: Critical Task (Council Review)

```
DIRECTOR determines task is CRITICAL
    │
    ├──► Normal tri-unit flow (Director → Executor → Guardian)
    │    → Result produced
    │
    └──► NATS: jart-os.04.study.council.proposals
         │
         ▼
     COUNCIL reviews (3 members)
         │
         ├── council-legal → NATS: jart-os.04.study.council.votes
         ├── council-pedagogical → NATS: jart-os.04.study.council.votes
         └── council-technical → NATS: jart-os.04.study.council.votes
              │
              ▼
         COUNCIL aggregates votes
              │
              ├── 3/3 PASS → NATS: jart-os.04.study.council.decisions (APPROVED)
              ├── 2/3 PASS → Depends on task type (normal = OK, critical = FAIL)
              └── 1/3 or Guardian VETO → NATS: jart-os.04.study.council.decisions (REJECTED)
                   → Back to EXECUTOR with feedback
```

### Flow 3: RAG Query

```
AGENT needs context
    │
    ├──► NATS: jart-os.06.pipeline.rag.query
    │    {
    │      "query": "topic 15 wines designation of origin",
    │      "top_k": 5,
    │      "filter": {"topic": 15, "type": "syllabus"},
    │      "collection": "study"
    │    }
    │
    ▼
PIPE-RAG queries Qdrant
    │
    ▼
Response (via NATS reply or Redis cache)
    {
      "results": [
        {"chunk": "...", "score": 0.92, "metadata": {"topic": 15, "source": "CEDE_Tomo2"}},
        ...
      ]
    }
```

---

## 5. Pipeline Communication Flows

### Flow 4: PDF Processing Pipeline

```
TRIGGER: NATS jart-os.06.pipeline.pdf.command
    {
      "action": "process_batch",
      "paths": ["/data/raw/pdfs/block_d/"],
      "options": {"deduplicate": true, "ocr_fallback": true}
    }
    │
    ▼
PIPE-PDF processes
    │
    ├── Stage 1: Classification → event (progress)
    ├── Stage 2: Text extraction → event (progress)
    ├── Stage 3: Cleaning → event (progress)
    ├── Stage 4: Deduplication → event (progress)
    ├── Stage 5: Structuring → event (progress)
    │
    └──► NATS: jart-os.06.pipeline.pdf.events (complete)
         │
         ▼
    PIPE-RAG picks up chunks automatically
         │
         ▼
    NATS: jart-os.06.pipeline.rag.command (index these chunks)
```

### Flow 5: Full Content Pipeline Orchestration

```
USER: "Process all study material"
    │
    ▼
DIRECTOR plans pipeline orchestration
    │
    ├──► NATS: jart-os.06.pipeline.pdf.command (start PDF)
    ├──► NATS: jart-os.06.pipeline.photos.command (start photos)
    └──► NATS: jart-os.06.pipeline.video.command (start video)
         │
         ├── Each pipeline publishes progress events
         └── When ALL complete → trigger RAG indexing
              │
              ▼
         NATS: jart-os.06.pipeline.rag.command (index all)
              │
              ▼
         NATS: jart-os.06.pipeline.rag.events (indexing complete)
              │
              ▼
         DIRECTOR notified → Study domain ready
```

---

## 6. Infrastructure Flows

### Flow 6: Health Check

```
Every 30 seconds, each service:
    │
    ├── Updates Redis key: jart-os:agent:<role>
    │   {status: "healthy", uptime: 3600, tasks_completed: 42}
    │
    └── Responds to NATS: jart-os.system.health
        {service: "director-study", status: "healthy"}
```

### Flow 7: LLM Call (Agent → LiteLLM)

```
AGENT needs LLM response
    │
    ▼
HTTP POST to LiteLLM (NOT through NATS)
    POST http://jart-os-litellm:4000/chat/completions
    Headers: Authorization: Bearer $LITELLM_KEY
    Body: {model: "glm-5", messages: [...], temperature: 0.7}
    │
    ▼
LiteLLM routes to provider (Z.AI / OpenRouter / Ollama)
    │
    ▼
Response → Agent processes
    │
    ▼
Agent logs to Redis: jart-os:audit:<task_id>
    {model, tokens_in, tokens_out, latency_ms, cost}
```

### Flow 8: State Persistence

```
AGENT updates task state → Redis
    │
    ├── SET jart-os:task:<task_id> {status, agent, started_at, ...}
    ├── SET jart-os:agent:<role> {status, uptime, tasks_completed}
    ├── SET jart-os:lock:<resource> (distributed mutex with TTL)
    └── SET jart-os:cache:<query_hash> (LLM response cache, TTL 1h)
```

---

## 7. External Integration Flows

### Flow 9: OpenCode → Docker (Planned)

```
OpenCode Skill needs Docker agent
    │
    ▼
NATS MCP Server (planned)
    │
    ├── Publish: jart-os.04.study.director.command
    └── Subscribe: jart-os.04.study.director.events
    │
    ▼
Docker agent processes task
    │
    ▼
OpenCode reads result from Redis: jart-os:task:<task_id>
```

### Flow 10: Telegram → OpenClaw → Agent (Planned)

```
User sends Telegram message
    │
    ▼
OpenClaw Gateway (:10202)
    │
    ▼
Parses intent → Routes to NATS
    jart-os.04.study.director.command
    │
    ▼
Agent processes → Result
    │
    ▼
OpenClaw formats → Telegram reply
```

### Flow 11: Mission Control → NATS

```
Mission Control web UI
    │
    ▼
HTTP API → NATS bridge
    │
    ├── Subscribe: jart-os.> (all events for dashboard)
    ├── Publish: jart-os.04.study.director.command (user actions)
    └── Query: Redis state (agent status, task progress)
```

---

## 8. Error Handling & Retries

### Retry Policy

```
FAILURE occurs (Guardian FAIL, timeout, LLM error)
    │
    ├── retry_count < max_retries (3)?
    │   ├── YES → Increment retry_count
    │   │        Add feedback to payload
    │   │        Re-publish to same subject
    │   └── NO → Escalate
    │            ├── If tri-unit: Notify Director
    │            └── If critical: Escalate to Council
    │
    └── Director decides: retry differently or abort
```

### Timeout Cascade

| Component | Timeout | On timeout |
|-----------|---------|------------|
| LLM call | 60s | Retry with different model |
| Guardian check | 120s | Mark as UNVERIFIED |
| Executor sub-task | 300s | Retry with feedback |
| Full task | 600s | Abort + notify Director |
| Pipeline batch | 3600s | Continue with partial results |

### Dead Letter

Failed messages after max retries → `jart-os.system.deadletter`
Monitor this subject for debugging.

---

## 9. Redis State Patterns

### Key Patterns

| Pattern | Type | TTL | Purpose |
|---------|------|-----|---------|
| `jart-os:task:<task_id>` | Hash | 24h | Task state and progress |
| `jart-os:agent:<role>` | Hash | 60s refresh | Agent heartbeat |
| `jart-os:lock:<resource>` | String | 30s (auto-expire) | Distributed mutex |
| `jart-os:cache:<hash>` | String | 1h | LLM response cache |
| `jart-os:ratelimit:<agent>` | Counter | 60s (sliding) | Token bucket rate limit |
| `jart-os:audit:<task_id>` | Hash | 30d | Audit trail |
| `jart-os:progress:<pipeline>` | Hash | 24h | Pipeline progress |

### Example: Task State

```json
// Redis key: jart-os:task:OP2-2026-TEM3-001
{
  "status": "executing",
  "agent": "executor-study",
  "started_at": "2026-04-16T12:00:00Z",
  "updated_at": "2026-04-16T12:03:00Z",
  "retry_count": 1,
  "model": "glm-4.7",
  "tokens_in": 2500,
  "tokens_out": 800,
  "cost_usd": 0.003
}
```

---

## 10. Monitoring & Observability

### NATS Monitoring

```bash
# NATS monitoring endpoint
curl http://localhost:10304/connz    # Connections
curl http://localhost:10304/routez   # Routes
curl http://localhost:10304/subsz    # Subscriptions
curl http://localhost:10304/streamz  # JetStream streams
```

### Prometheus Metrics

Each agent exposes `/metrics` endpoint (Prometheus format):

```
# HELP jart_os_tasks_total Total tasks processed
# TYPE jart_os_tasks_total counter
jart_os_tasks_total{agent="director",domain="study",status="completed"} 42

# HELP jart_os_llm_calls_total LLM API calls
# TYPE jart_os_llm_calls_total counter
jart_os_llm_calls_total{model="glm-5",status="success"} 128

# HELP jart_os_task_duration_seconds Task duration
# TYPE jart_os_task_duration_seconds histogram
jart_os_task_duration_seconds{agent="executor"} 12.5
```

### Grafana Dashboards

| Dashboard | Panels |
|-----------|--------|
| Agent Overview | Task throughput, latency, error rate per agent |
| LLM Usage | Tokens per model, cost tracking, rate limits |
| Pipeline Progress | Files processed, chunks generated, queue depth |
| System Health | Container status, Redis memory, NATS connections |

### Audit Trail

Every task logged to Redis with:
- Agent, model, tokens, duration, verdict, retry_count, timestamps
- Queryable via `jart-os:audit:<task_id>` pattern
- Retention: 30 days

---

*Distilled from CANONICAL-SPEC §12 + AGENT_PROTOCOL.md + OPENCLAW-system messaging specs.*
