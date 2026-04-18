"""A2A Protocol — Agent Card definition."""

AGENT_CARD = {
    "name": "MCP-jart-os-agent-{function}",
    "description": "{FUNCTION_DESCRIPTION}",
    "url": "http://{host}:{port}/a2a",
    "version": "0.1.0",
    "capabilities": {
        "streaming": True,
        "pushNotifications": True,
    },
    "skills": [
        # Populated dynamically from registered MCP tools
        # Each tool becomes an A2A skill
    ],
    "defaultInputModes": ["text/plain", "application/json"],
    "defaultOutputModes": ["text/plain", "application/json"],
}
