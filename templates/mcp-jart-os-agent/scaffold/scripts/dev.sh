#!/usr/bin/env bash
# Development runner for MCP-jart-os-agent-{function}
#
# Usage: bash scripts/dev.sh [stdio|http]
set -euo pipefail

MODE="${1:-stdio}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Load .env if exists
if [ -f config/.env ]; then
    set -a
    source config/.env
    set +a
fi

case "$MODE" in
    stdio)
        echo "Starting MCP server (stdio transport)..." >&2
        MCP_TRANSPORT=stdio python -m src.main
        ;;
    http)
        MCP_PORT="${MCP_PORT:-8080}"
        A2A_PORT="${A2A_PORT:-8081}"
        HEALTH_PORT="${HEALTH_PORT:-9090}"
        echo "Starting MCP server (HTTP transport)..." >&2
        echo "  MCP:      http://localhost:${MCP_PORT}" >&2
        echo "  A2A:      http://localhost:${A2A_PORT}" >&2
        echo "  Health:   http://localhost:${HEALTH_PORT}/health" >&2
        echo "  Metrics:  http://localhost:${HEALTH_PORT}/metrics" >&2
        MCP_TRANSPORT=streamable-http \
        MCP_PORT="${MCP_PORT}" \
        A2A_ENABLED=true \
        A2A_PORT="${A2A_PORT}" \
        HEALTH_PORT="${HEALTH_PORT}" \
        python -m src.main
        ;;
    *)
        echo "Usage: bash scripts/dev.sh [stdio|http]" >&2
        exit 1
        ;;
esac
