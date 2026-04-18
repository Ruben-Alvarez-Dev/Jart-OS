# MCP-jart-os-agent-{function}

> Jart-OS agent backpack: {FUNCTION_DESCRIPTION}

## Overview

This is a Jart-OS agent backpack MCP server, generated from `TEMPLATE-mcp-jart-os-agent`.

It implements 3 layers:

| Layer | Description |
|-------|-------------|
| **Layer 1: Industry Standards** | MCP Protocol (FastMCP) + A2A Protocol (Agent Card) + MCP Apps (optional) |
| **Layer 2: Jart-OS Federation** | NATS messaging + Redis state + Governance + Observability |
| **Layer 3: {FUNCTION}** | Specific tools — `← YOUR IMPLEMENTATION HERE` |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp config/.env.example config/.env
# Edit config/.env with your values

# Run (stdio transport — default for MCP)
python -m src.main

# Run (HTTP transport — for A2A + observability)
MCP_TRANSPORT=streamable-http MCP_PORT=8080 python -m src.main
```

## Docker

```bash
docker compose up -d
```

## Tools

| Tool | Description |
|------|-------------|
| `tool_example` | Placeholder — replace with {function} tools |

> **TODO**: Replace this table with your actual tools from `src/tools/{function}.py`.

## Configuration

See `config/.env.example` for all available environment variables.

## Compliance

This server complies with:

- [x] MCP Protocol (spec 2025-11-25)
- [x] A2A Protocol (v1.0.0)
- [ ] MCP Apps (optional — implement if tools need UI)
- [x] Jart-OS Federation (NATS + Redis + Governance)

## Testing

```bash
# Run all tests
bash scripts/test.sh

# Run specific test suite
pytest tests/test_mcp_compliance.py -v
```

## Structure

```
src/
├── main.py              # Entry point
├── server.py            # FastMCP server + lifespan
├── config.py            # Environment settings
├── a2a/                 # A2A protocol (Layer 1)
├── federation/          # Jart-OS federation (Layer 2)
├── tools/               # {FUNCTION} tools (Layer 3) ← YOUR CODE
└── models/              # Pydantic schemas
```

## License

See LICENSE file.
