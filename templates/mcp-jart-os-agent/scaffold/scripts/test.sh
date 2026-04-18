#!/usr/bin/env bash
# Test runner for MCP-jart-os-agent-{function}
#
# Usage: bash scripts/test.sh [suite]
#   suite: all | mcp | a2a | federation | function
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Ensure test dependencies
pip install -q pytest pytest-asyncio httpx 2>/dev/null || true

SUITE="${1:-all}"

case "$SUITE" in
    all)
        echo "Running ALL tests..." >&2
        pytest tests/ -v --tb=short
        ;;
    mcp)
        echo "Running MCP compliance tests..." >&2
        pytest tests/test_mcp_compliance.py -v --tb=short
        ;;
    a2a)
        echo "Running A2A compliance tests..." >&2
        pytest tests/test_a2a_compliance.py -v --tb=short
        ;;
    federation)
        echo "Running Federation tests..." >&2
        pytest tests/test_federation.py -v --tb=short
        ;;
    function)
        echo "Running {function} tests..." >&2
        pytest tests/test_template.py -v --tb=short
        ;;
    *)
        echo "Usage: bash scripts/test.sh [all|mcp|a2a|federation|function]" >&2
        exit 1
        ;;
esac
