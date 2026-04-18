"""Template tools — REPLACE with {function}-specific tools.

This file is a placeholder showing the pattern for tool implementation.
Each backpack replaces this with its own tools module.

Tools must:
- Use Pydantic input/output types from src/models/schemas.py
- Accept Context parameter for logging/progress
- Include docstrings (visible to the LLM via MCP)
- Return structured output (not raw strings)
"""

from __future__ import annotations

from mcp.server.fastmcp import Context

from src.models.schemas import (
    TemplateInput,
    TemplateOutput,
)


async def tool_example(input: TemplateInput, ctx: Context) -> TemplateOutput:
    """Example tool — replace with actual {function} tools.

    Args:
        input: Validated input via Pydantic model.
        ctx: MCP context for logging and progress reporting.

    Returns:
        Structured output via Pydantic model.
    """
    await ctx.info(f"tool_example called with: {input.query}")

    # === LAYER 3: YOUR LOGIC HERE ===
    result = {"message": f"Processed: {input.query}"}

    return TemplateOutput(
        status="ok",
        data=result,
    )
