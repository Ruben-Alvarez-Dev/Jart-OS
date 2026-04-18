"""Pydantic schemas for tool structured output.

Every MCP tool MUST return a Pydantic model for structured output.
This is a MCP Protocol requirement (Layer 1 compliance).

Replace TemplateInput/TemplateOutput with your {function}-specific models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# === Template models — REPLACE with {function}-specific models ===


class TemplateInput(BaseModel):
    """Input model for template tool."""

    query: str = Field(..., description="The query to process")
    options: dict | None = Field(
        default=None,
        description="Optional parameters",
    )


class TemplateOutput(BaseModel):
    """Output model for template tool."""

    status: str = Field(..., description="Result status: ok | error")
    data: dict | None = Field(
        default=None,
        description="Result payload",
    )
    error: str | None = Field(
        default=None,
        description="Error message if status=error",
    )
