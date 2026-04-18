# Jart-OS Standards Compliance

> **Status**: Stable  
> **Version**: 1.0.0  
> **Last updated**: 2026-04-18  
> **Mandatory**: YES — no exceptions

This document defines the **mandatory industry standards** that ALL Jart-OS components must comply with. These are non-negotiable prerequisites — no Jart-OS specific code is written without full compliance first.

---

## The Three Standards

| Standard | Origin | Governance | Version | Purpose |
|----------|--------|-----------|---------|---------|
| **MCP Protocol** | Anthropic | Linux Foundation | 2025-11-25 | Agent uses TOOLS (backpack) |
| **A2A Protocol** | Google | Linux Foundation | v1.0.0 (2026-03) | Agent ↔ Agent communication |
| **MCP Apps** | Anthropic | modelcontextprotocol | v1.6.0 (2026-01) | Tool presents UI to user |

All three are **complementary, not competing**. They solve different problems. All three are open source under permissive licenses (MIT / Apache 2.0).

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│ Layer 3: Specific Function                          │
│   Memory tools, Search tools, Infra tools, etc.     │
├─────────────────────────────────────────────────────┤
│ Layer 2: Jart-OS Federation                         │
│   NATS messaging, Redis state, Spec gates,          │
│   Quality gates, Governance, Audit trail            │
├─────────────────────────────────────────────────────┤
│ Layer 1: Industry Standards — MANDATORY             │
│   ┌───────────┐  ┌──────────┐  ┌──────────────┐   │
│   │ MCP       │  │ A2A      │  │ MCP Apps     │   │
│   │ Protocol  │  │ Protocol │  │ (UI)         │   │
│   └───────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Rule**: You cannot implement Layer 2 or Layer 3 without completing Layer 1.

---

## 1. MCP Protocol — Tool Exposure

### Spec Location
- Repository: `modelcontextprotocol/specification`
- Python SDK: `modelcontextprotocol/python-sdk` (v1.x stable)
- Schema: TypeScript-first, available as JSON Schema

### Required Features for Jart-OS MCP Servers

| Feature | API | Required? | Notes |
|---------|-----|-----------|-------|
| **Tools** | `@mcp.tool()` | ✅ Mandatory | Core — every server exposes tools |
| **Resources** | `@mcp.resource()` | ✅ Mandatory | Expose data to LLMs |
| **Prompts** | `@mcp.prompt()` | 🟡 Recommended | Reusable interaction templates |
| **Structured Output** | Return type annotations | ✅ Mandatory | All tools return typed data (Pydantic) |
| **Context** | `ctx.info()`, `ctx.report_progress()` | ✅ Mandatory | Logging, progress, notifications |
| **Elicitation** | `ctx.elicit()` | 🟡 Recommended | Request user input mid-task |
| **Sampling** | `ctx.session.create_message()` | ⬜ Optional | LLM text generation from tool |
| **Authentication** | `TokenVerifier` + OAuth 2.1 | ✅ Mandatory | For any exposed server |
| **Completions** | Via context | 🟡 Recommended | Autocomplete for arguments |
| **Icons** | `Icon(src=...)` | 🟡 Recommended | UI display metadata |
| **Transport** | stdio, SSE, streamable-http | ✅ Mandatory | stdio for local, HTTP for remote |

### Transport Requirements
- **stdio**: For local MCP client connections (Claude Desktop, OpenCode, etc.)
- **Streamable HTTP**: For remote connections (Jart-OS federation, web clients)
- **ASGI mounting**: For embedding in existing web servers

### Minimum Viable MCP Server
```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("server-name", json_response=True)

class ToolResult(BaseModel):
    status: str
    data: dict

@mcp.tool()
def my_tool(param: str) -> ToolResult:
    """Description visible to the LLM."""
    return ToolResult(status="ok", data={"result": param})
```

---

## 2. A2A Protocol — Agent-to-Agent Communication

### Spec Location
- Repository: `a2aproject/A2A` (Linux Foundation)
- Python SDK: `pip install a2a-sdk`
- Go SDK: `go get github.com/a2aproject/a2a-go`
- JS SDK: `npm install @a2a-js/sdk`

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent Card** | JSON document describing agent capabilities, connection info, authentication |
| **Task** | Unit of work: created, assigned, executed, completed |
| **Message** | Communication within a task (text, files, structured data) |
| **Streaming** | SSE-based real-time updates on task progress |
| **Push Notifications** | Async notifications for long-running tasks |

### A2A vs MCP — When to use which

| Scenario | Protocol | Why |
|----------|----------|-----|
| Agent needs to store/retrieve memory | **MCP** | Memory is a TOOL the agent uses |
| Agent needs to search the web | **MCP** | Search is a TOOL the agent uses |
| Director delegates task to Executor | **A2A** | Agent-to-agent task delegation |
| Guardian validates Executor's output | **A2A** | Agent-to-agent review |
| Council votes on a decision | **A2A** | Agent-to-agent consensus |
| Memory server reports status to Director | **A2A** | Agent-to-agent status update |

### Required A2A Features for Jart-OS

| Feature | Required? | Notes |
|---------|-----------|-------|
| **Agent Card exposure** | ✅ Mandatory | Every agent publishes its capabilities |
| **Task creation/handling** | ✅ Mandatory | Core A2A functionality |
| **Message exchange** | ✅ Mandatory | Text + structured data within tasks |
| **Streaming (SSE)** | 🟡 Recommended | Real-time progress updates |
| **Push notifications** | 🟡 Recommended | Long-running task updates |
| **Authentication** | ✅ Mandatory | Secure agent-to-agent communication |

### Minimum Viable A2A Agent Card
```json
{
  "name": "MCP-jartos-agent-memory",
  "description": "Memory backpack for Jart-OS agents",
  "url": "http://memory:10401/a2a",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {
      "name": "store-memory",
      "description": "Store information in agent's memory"
    },
    {
      "name": "recall-memory",
      "description": "Recall stored information"
    }
  ]
}
```

---

## 3. MCP Apps — Interactive UI

### Spec Location
- Repository: `modelcontextprotocol/ext-apps`
- SDK: `npm install @modelcontextprotocol/ext-apps`
- Spec version: 2026-01-26 (stable)

### When to use MCP Apps
- When a tool needs to show a **chart, form, dashboard, or interactive visualization**
- When the user needs to **interact** with tool output (not just read text)
- When the tool benefits from **visual representation** of data

### Required MCP Apps Features for Jart-OS

| Feature | Required? | Notes |
|---------|-----------|-------|
| **Tool ui:// resource declaration** | 🟡 If tool has UI | Tools declare their UI via `ui://` URIs |
| **HTML/React/Vue/etc. view** | 🟡 If tool has UI | Rendered in sandboxed iframe |
| **Bidirectional communication** | 🟡 If tool has UI | Host ↔ UI data exchange |

### Applicable Jart-OS Components

| Component | Needs MCP Apps? | What UI |
|-----------|----------------|---------|
| MCP-jartos-agent-memory | 🟡 Maybe | Memory browser, search results visualization |
| Mission Control | ✅ Yes | Real-time agent status, pipeline progress |
| MCP-jartos-agent-search | 🟡 Maybe | Search results with filters, document preview |
| CLI-jartos | ❌ No | CLI is terminal-based |

---

## Compliance Checklist

Every MCP-jartos-agent-* must pass this checklist before being accepted into Jart-OS:

### MCP Compliance
- [ ] FastMCP server with proper tool/resource/prompt definitions
- [ ] All tools have structured output (Pydantic models)
- [ ] Context support (logging, progress reporting)
- [ ] Both stdio and streamable-http transports
- [ ] OAuth 2.1 authentication for HTTP transport
- [ ] `.jart-manifest` with compliance declaration

### A2A Compliance
- [ ] Agent Card published and accessible
- [ ] Task creation and handling endpoints
- [ ] Message exchange (text + structured data)
- [ ] Authentication on A2A endpoints
- [ ] Capability discovery via Agent Card

### MCP Apps Compliance (if applicable)
- [ ] `ui://` resources declared for tools with UI
- [ ] Interactive views render correctly in compliant hosts
- [ ] Bidirectional communication between host and view

### Jart-OS Federation (Layer 2)
- [ ] NATS connection and subject subscription
- [ ] Redis connection for state management
- [ ] Spec gate validation (pre-execution)
- [ ] Quality gate validation (post-execution)
- [ ] Audit trail logging
- [ ] Health/metrics/state HTTP endpoints

---

## Reference Links

| Resource | URL |
|----------|-----|
| MCP Specification | https://modelcontextprotocol.io/specification/latest |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk |
| MCP TypeScript SDK | https://github.com/modelcontextprotocol/typescript-sdk |
| MCP Apps SDK | https://github.com/modelcontextprotocol/ext-apps |
| A2A Protocol | https://github.com/a2aproject/A2A |
| A2A Documentation | https://a2a-protocol.org |
| A2A Python SDK | https://github.com/a2aproject/a2a-python |
| A2A Go SDK | https://github.com/a2aproject/a2a-go |
| A2A JS SDK | https://github.com/a2aproject/a2a-js |
| MCP Apps Quickstart | https://apps.extensions.modelcontextprotocol.io/api/documents/Quickstart.html |
