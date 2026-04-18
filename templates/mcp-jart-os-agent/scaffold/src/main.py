"""
MCP-jart-os-agent-{function} — Entry Point
Boot sequence: MCP server + A2A endpoint + Jart-OS federation

Layer 1: MCP Protocol (FastMCP) + A2A Protocol
Layer 2: Jart-OS Federation (NATS, Redis, governance)
Layer 3: {FUNCTION_DESCRIPTION}
"""

import asyncio
import logging
import os
import signal

from src.server import mcp
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
log = logging.getLogger(f"jart-os.{settings.function}")


def boot():
    """
    Boot sequence:
    1. Start MCP server (FastMCP)
    2. Start A2A endpoint (if enabled)
    3. Connect Jart-OS federation (NATS + Redis)
    4. Register signal handlers for graceful shutdown
    """
    log.info(
        f"Booting MCP-jart-os-agent-{settings.function} "
        f"transport={settings.mcp_transport}"
    )

    # Signal handlers
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    # Start FastMCP server (blocks until shutdown)
    mcp.run(transport=settings.mcp_transport)


def _shutdown(signum, frame):
    """Graceful shutdown handler."""
    log.info(f"Received signal {signum}, shutting down...")
    # Federation cleanup handled by lifespan in server.py
    raise SystemExit(0)


if __name__ == "__main__":
    boot()
