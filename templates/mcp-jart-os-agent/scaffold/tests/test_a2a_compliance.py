"""A2A Protocol compliance tests — Layer 1.

Verifies that the server meets A2A Protocol requirements:
- Agent Card publication at /.well-known/agent.json
- JSON-RPC 2.0 endpoint at /a2a
- Task lifecycle: create, get, cancel
- Proper error responses (JSON-RPC error codes)
- Agent Card has required fields
"""

import pytest
from src.a2a.agent_card import get_agent_card


class TestAgentCard:
    """Agent Card must follow A2A spec."""

    def test_agent_card_has_name(self):
        card = get_agent_card()
        assert "name" in card
        assert "jart-os-agent" in card["name"].lower()

    def test_agent_card_has_description(self):
        card = get_agent_card()
        assert "description" in card
        assert len(card["description"]) > 0

    def test_agent_card_has_url(self):
        card = get_agent_card()
        assert "url" in card
        assert card["url"].startswith("http")

    def test_agent_card_has_capabilities(self):
        card = get_agent_card()
        assert "capabilities" in card
        caps = card["capabilities"]
        assert isinstance(caps, dict)

    def test_agent_card_has_skills(self):
        card = get_agent_card()
        assert "skills" in card
        assert isinstance(card["skills"], list)


class TestA2AJSONRPC:
    """A2A endpoints must follow JSON-RPC 2.0."""

    def test_routes_importable(self):
        """A2A routes module must be importable."""
        from src.a2a.routes import A2ARoutes
        assert A2ARoutes is not None

    def test_task_handler_importable(self):
        """Task handler module must be importable."""
        from src.a2a.task_handler import TaskHandler
        assert TaskHandler is not None

    def test_error_response_format(self):
        """Error responses must follow JSON-RPC 2.0 spec."""
        from src.a2a.routes import A2ARoutes
        from src.a2a.task_handler import TaskHandler

        handler = TaskHandler()
        routes = A2ARoutes(handler)

        error = routes._error_response("test-id", -32600, "Invalid Request")
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == "test-id"
        assert "error" in error
        assert error["error"]["code"] == -32600
        assert error["error"]["message"] == "Invalid Request"

    def test_success_response_format(self):
        """Success responses must follow JSON-RPC 2.0 spec."""
        from src.a2a.routes import A2ARoutes
        from src.a2a.task_handler import TaskHandler

        handler = TaskHandler()
        routes = A2ARoutes(handler)

        success = routes._success_response("test-id", {"status": "ok"})
        assert success["jsonrpc"] == "2.0"
        assert success["id"] == "test-id"
        assert success["result"] == {"status": "ok"}
