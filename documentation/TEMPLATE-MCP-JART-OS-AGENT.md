# Template: MCP-jart-os-agent

> **Status**: Draft  
> **Version**: 0.1.0  
> **Last updated**: 2026-04-18  
> **Generates**: `MCP-jart-os-agent-{function}` (memory, search, infra, etc.)

This document defines the template for creating Jart-OS agent backpack MCP servers. Every `MCP-jart-os-agent-*` is generated from this template.

---

## Architecture: 3 Layers

```
┌─────────────────────────────────────────────────────┐
│ Layer 3: {FUNCTION}                                  │
│   Tools specific to this backpack                    │
│   memory: add, search, delete, consolidate           │
│   search: web, documents, code                       │
│   infra: docker_status, service_health               │
├─────────────────────────────────────────────────────┤
│ Layer 2: Jart-OS Federation                          │
│   NATS messaging + Redis state + Governance +        │
│   Audit trail + Health/Metrics/State endpoints       │
├─────────────────────────────────────────────────────┤
│ Layer 1: Industry Standards                          │
│   MCP Protocol (FastMCP) + A2A Protocol (agent card) │
│   + MCP Apps (optional UI)                           │
│   See STANDARDS.md for full compliance checklist     │
└─────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
MCP-jart-os-agent-{function}/
├── src/
│   ├── main.py                   # Entry point: FastMCP + A2A + boot
│   ├── server.py                 # FastMCP server definition + lifespan
│   ├── a2a/
│   │   ├── __init__.py
│   │   ├── agent_card.py         # Agent Card (JSON spec)
│   │   ├── task_handler.py       # A2A task lifecycle
│   │   └── routes.py             # A2A HTTP endpoints (JSON-RPC 2.0)
│   ├── federation/
│   │   ├── __init__.py
│   │   ├── nats_client.py        # NATS connection + subject subscription
│   │   ├── redis_client.py       # Redis state management
│   │   ├── governance.py         # Spec gate + quality gate + audit trail
│   │   └── observability.py      # /health, /metrics, /state endpoints
│   ├── tools/
│   │   ├── __init__.py
│   │   └── {function}.py         # ← REPLACE: specific tools
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic models for structured output
│   └── config.py                 # Environment + settings
├── ui/                           # MCP Apps (optional, if tool has UI)
│   └── {function}-app/           # React/Vue/Svelte app
├── tests/
│   ├── test_mcp_compliance.py    # MCP protocol compliance tests
│   ├── test_a2a_compliance.py    # A2A protocol compliance tests
│   ├── test_federation.py        # Jart-OS federation tests
│   └── test_{function}.py        # Specific function tests
├── config/
│   └── .env.example              # Environment variables template
├── scripts/
│   ├── dev.sh                    # Run in development mode
│   └── test.sh                   # Run all tests
├── Dockerfile                    # Container build
├── docker-compose.yml            # Local development stack
├── requirements.txt              # Python dependencies
├── README.md                     # Server documentation
├── CHANGELOG.md                  # Version history
├── VERSION                       # Current version (semver)
└── .jart-os-manifest                # Jart-OS metadata
```

---

## Layer 1: Industry Standards Implementation

### 1a. MCP Protocol (FastMCP)

**File**: `src/server.py`

```python
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel

mcp = FastMCP(
    "MCP-jart-os-agent-{function}",
    json_response=True,
    instructions="Jart-OS agent backpack: {FUNCTION_DESCRIPTION}",
)

# Tools are registered in src/tools/{function}.py
# They must:
# - Have Pydantic return types (structured output)
# - Accept Context parameter for logging/progress
# - Include docstrings (visible to LLM)
```

**Required dependencies** (requirements.txt):
```
mcp[cli]>=1.0.0
pydantic>=2.0
```

### 1b. A2A Protocol

**File**: `src/a2a/agent_card.py`

Every backpack publishes an Agent Card describing its capabilities. The card is served at `/.well-known/agent.json` per A2A spec.

```python
AGENT_CARD = {
    "name": "MCP-jart-os-agent-{function}",
    "description": "{FUNCTION_DESCRIPTION}",
    "url": "http://{host}:{port}/a2a",
    "capabilities": {
        "streaming": True,
        "pushNotifications": True,
    },
    "skills": [
        # Populated from registered MCP tools
    ]
}
```

**File**: `src/a2a/routes.py`

A2A endpoints follow JSON-RPC 2.0 over HTTP:
- `POST /a2a` — Main JSON-RPC endpoint
- `GET /.well-known/agent.json` — Agent Card discovery
- `GET /a2a/tasks/{id}` — Task status
- `POST /a2a/tasks/{id}/cancel` — Cancel task

**Required dependencies**:
```
a2a-sdk>=1.0.0
```

### 1c. MCP Apps (Optional)

**Directory**: `ui/{function}-app/`

Only if the backpack's tools benefit from interactive UI. Uses `@modelcontextprotocol/ext-apps` SDK.

Tools declare UI via `ui://` resources:
```python
@mcp.tool()
async def my_tool_with_ui(data: str, ctx: Context) -> str:
    """Tool that shows an interactive visualization."""
    return result  # UI rendered separately via ui:// resource
```

---

## Layer 2: Jart-OS Federation Implementation

### NATS Client

**File**: `src/federation/nats_client.py`

Connects to Jart-OS NATS JetStream for inter-service messaging.

- Subject prefix: `jart-os.{tier}.{domain}.{function}`
- Subscribes to: `jart-os.04.*.director.task.assign` (receive tasks from director)
- Publishes to: `jart-os.04.{function}.{role}.task.complete` (report completion)
- Message format: Standard envelope (task_id, from, to, timestamp, payload, metadata)
- See: `documentation/COMMUNICATION-FLOWS.md` for full spec

### Redis Client

**File**: `src/federation/redis_client.py`

Manages state in Jart-OS Redis instance.

- Key prefix: `jart-os:{function}:`
- Patterns: `{function}:task:{id}`, `{function}:cache:{key}`, `{function}:state:{agent_id}`
- Pub/Sub: `{function}:events`
- See: `documentation/API-REFERENCE.md` for key patterns

### Governance

**File**: `src/federation/governance.py`

Validates tasks against spec gates:

- **Pre-execution**: Load `agents/policies/spec-gate.yaml`, validate every task envelope before processing
- **Post-execution**: Load `agents/policies/quality-gate.yaml`, validate results before reporting
- **Audit trail**: Write to Redis key `jart-os:audit:{task_id}` with full lifecycle events
- See: `agents/policies/spec-gate.yaml` (108 lines, 8 rules) and `agents/policies/quality-gate.yaml` (74 lines)

### Observability

**File**: `src/federation/observability.py`

HTTP endpoints following AgentBase v3.0 pattern:

- `GET /health` — `{status, role, domain, tier, uptime}`
- `GET /metrics` — Prometheus-format metrics
- `GET /state` — `{tasks_completed, tasks_failed, current_task, nats_connected, redis_connected, uptime}`

---

## Layer 3: Specific Function

**File**: `src/tools/{function}.py`

This is the ONLY file that changes between different backpacks. Everything else is shared.

```python
from mcp.server.fastmcp import Context
from src.models.schemas import (
    {Function}Input,
    {Function}Output,
)

# Each tool follows the same pattern:
# - Pydantic input/output types
# - Context parameter for logging/progress
# - Docstring for LLM discovery

async def tool_{action}(input: {Function}Input, ctx: Context) -> {Function}Output:
    """Tool description visible to the LLM."""
    await ctx.info(f"Starting {action}")
    # ... implementation
    return {Function}Output(status="ok", data=result)
```

**Examples of function-specific tools:**

| Backpack | Tools |
|----------|-------|
| `MCP-jart-os-agent-memory` | `add_memory`, `search_memory`, `delete_memory`, `consolidate` |
| `MCP-jart-os-agent-search` | `web_search`, `document_search`, `code_search` |
| `MCP-jart-os-agent-infra` | `docker_status`, `service_health`, `logs` |

---

## Configuration

### Environment Variables (.env.example)

```env
# MCP Server
MCP_TRANSPORT=stdio                    # stdio | streamable-http
MCP_PORT=0                             # 0 = auto-assign
MCP_HOST=0.0.0.0

# A2A Protocol
A2A_ENABLED=true
A2A_HOST=0.0.0.0
A2A_PORT=0

# Jart-OS Federation
NATS_URL=nats://nats:4222
REDIS_URL=redis://redis:6379
LITELLM_URL=http://litellm:4000
LITELLM_KEY=REDACTED_LITELLM_KEY

# Governance
SPEC_GATE_PATH=/app/policies/spec-gate.yaml
QUALITY_GATE_PATH=/app/policies/quality-gate.yaml

# Observability
HEALTH_PORT=0
METRICS_ENABLED=true

# Function-specific
# {FUNCTION}_SPECIFIC_VAR=default
```

### .jart-os-manifest

```json
{
  "version": "0.1.0",
  "category": "mcp",
  "subcategory": "jart-os-agent",
  "function": "{function}",
  "stack": {
    "language": "python",
    "runtime": "fastmcp",
    "protocols": ["mcp", "a2a"],
    "mcp_apps": false
  },
  "compliance": {
    "mcp_protocol": "2025-11-25",
    "a2a_protocol": "v1.0.0",
    "mcp_apps": null,
    "jart_os_federation": true
  },
  "jart-os": {
    "tier": 4,
    "domain": "agents",
    "role": "backpack",
    "nats_subjects": ["jart-os.04.{function}.*"],
    "redis_prefix": "jart-os:{function}:"
  }
}
```

---

## Usage: Generate a New Backpack

```bash
# Future: CLI generates from template
CLI-jart-os scaffold mcp-jart-os-agent memory

# Manual: Copy scaffold and replace {function} placeholders
cp -r templates/mcp-jart-os-agent/scaffold/ PROJECT-MCP-jart-os-agent-{function}/
# Replace all {function}, {Function}, {FUNCTION} placeholders
# Implement src/tools/{function}.py
# Write tests in tests/test_{function}.py
```

---

## Testing Requirements

Every generated backpack must pass:

1. **MCP compliance tests** — Verify tool registration, structured output, context support
2. **A2A compliance tests** — Verify agent card, task handling, message format
3. **Federation tests** — Verify NATS/Redis connection, governance validation, audit trail
4. **Function tests** — Verify specific tool behavior

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-04-18 | Initial template design |
