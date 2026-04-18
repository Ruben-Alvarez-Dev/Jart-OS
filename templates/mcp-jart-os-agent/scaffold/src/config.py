"""
Configuration — Environment + Settings

All configuration via environment variables with sensible defaults.
No hardcoded secrets, no magic values.
"""

import os


class Settings:
    """Application settings from environment."""

    # Identity
    function: str = os.getenv("FUNCTION_NAME", "{function}")

    # MCP Protocol (Layer 1a)
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "stdio")
    mcp_port: int = int(os.getenv("MCP_PORT", "0"))
    mcp_host: str = os.getenv("MCP_HOST", "0.0.0.0")

    # A2A Protocol (Layer 1b)
    a2a_enabled: bool = os.getenv("A2A_ENABLED", "true").lower() == "true"
    a2a_host: str = os.getenv("A2A_HOST", "0.0.0.0")
    a2a_port: int = int(os.getenv("A2A_PORT", "0"))

    # Jart-OS Federation (Layer 2)
    nats_url: str = os.getenv("NATS_URL", "nats://nats:4222")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    litellm_url: str = os.getenv("LITELLM_URL", "http://litellm:4000")
    litellm_key: str = os.getenv("LITELLM_KEY", "REDACTED_LITELLM_KEY")

    # Governance
    spec_gate_path: str = os.getenv(
        "SPEC_GATE_PATH", "/app/policies/spec-gate.yaml"
    )
    quality_gate_path: str = os.getenv(
        "QUALITY_GATE_PATH", "/app/policies/quality-gate.yaml"
    )

    # Observability
    health_port: int = int(os.getenv("HEALTH_PORT", "0"))
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"

    # Jart-OS identity
    tier: int = int(os.getenv("JARTOS_TIER", "4"))
    domain: str = os.getenv("JARTOS_DOMAIN", "agents")
    role: str = os.getenv("JARTOS_ROLE", "backpack")


settings = Settings()
