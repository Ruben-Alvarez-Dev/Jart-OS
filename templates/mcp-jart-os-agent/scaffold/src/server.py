"""
MCP-jart-os-agent-{function} — FastMCP Server Definition

Layer 1: MCP Protocol compliance
- Tools with structured output (Pydantic)
- Resources for data exposure
- Context support (logging, progress, notifications)
- Elicitation for user interaction
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from src.federation.nats_client import NATSClient
from src.federation.redis_client import RedisClient
from src.federation.governance import GovernanceManager
from src.federation.observability import ObservabilityServer
from src.config import settings


# ─────────────────────────────────────────────────────────
# Lifespan: startup/shutdown for federation connections
# ─────────────────────────────────────────────────────────

@dataclass
class AppContext:
    """Typed context for lifespan dependencies."""
    nats: NATSClient
    redis: RedisClient
    governance: GovernanceManager
    observability: ObservabilityServer


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Layer 2: Jart-OS Federation lifecycle.
    Connect NATS → Redis → Governance → Observability on startup.
    Disconnect all on shutdown.
    """
    import logging
    log = logging.getLogger(f"jart-os.{settings.function}")

    # Connect Layer 2 services
    nats = NATSClient()
    redis = RedisClient()
    governance = GovernanceManager()
    observability = ObservabilityServer()

    try:
        await nats.connect()
        await redis.connect()
        await governance.load_policies()
        await observability.start()

        log.info("Federation layer connected (NATS + Redis + Governance)")

        yield AppContext(
            nats=nats,
            redis=redis,
            governance=governance,
            observability=observability,
        )
    finally:
        await observability.stop()
        await nats.disconnect()
        await redis.disconnect()
        log.info("Federation layer disconnected")


# ─────────────────────────────────────────────────────────
# FastMCP Server Instance
# ─────────────────────────────────────────────────────────

mcp = FastMCP(
    f"MCP-jart-os-agent-{settings.function}",
    json_response=True,
    instructions="{FUNCTION_DESCRIPTION}",
    lifespan=app_lifespan,
)


# Tools are imported and registered in src/tools/__init__.py
# This ensures all tools have access to the federation context
from src.tools import register_tools  # noqa: E402, F401
register_tools(mcp)
