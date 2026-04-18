"""MCP Protocol compliance tests — Layer 1.

Verifies that the server meets MCP Protocol requirements:
- Tool registration with proper names
- Structured output (Pydantic return types)
- Context parameter support
- Docstrings for LLM discovery
- Server metadata (name, instructions)
"""

import pytest
from mcp.server.fastmcp import FastMCP

from src.server import mcp


class TestMCPServerMetadata:
    """Server must have correct name and instructions."""

    def test_server_has_name(self):
        assert mcp.name is not None
        assert "jart-os-agent" in mcp.name.lower()

    def test_server_has_instructions(self):
        assert mcp.instructions is not None
        assert len(mcp.instructions) > 0


class TestToolRegistration:
    """Tools must be properly registered with the MCP server."""

    def test_tools_registered(self):
        """At least one tool should be registered."""
        # FastMCP stores tools internally; verify the list is non-empty
        # after server is configured
        tools = mcp._tool_manager.list_tools()
        assert len(tools) > 0, "No tools registered — implement src/tools/"

    def test_tools_have_names(self):
        """Every tool must have a descriptive name."""
        tools = mcp._tool_manager.list_tools()
        for tool in tools:
            assert tool.name is not None
            assert len(tool.name) > 0
            # Tool names should be snake_case
            assert " " not in tool.name

    def test_tools_have_docstrings(self):
        """Every tool must have a docstring for LLM discovery."""
        tools = mcp._tool_manager.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0, (
                f"Tool '{tool.name}' missing docstring"
            )


class TestStructuredOutput:
    """Tools must return Pydantic models for structured output."""

    def test_models_importable(self):
        """Schema models must be importable."""
        from src.models.schemas import TemplateOutput
        assert TemplateOutput is not None

    def test_output_model_has_status(self):
        """Output model must have a status field."""
        from src.models.schemas import TemplateOutput
        fields = TemplateOutput.model_fields
        assert "status" in fields, "Output model must have 'status' field"

    def test_output_model_instantiates(self):
        """Output model must be instantiable with valid data."""
        from src.models.schemas import TemplateOutput
        result = TemplateOutput(status="ok", data={"key": "value"})
        assert result.status == "ok"
        assert result.data == {"key": "value"}
