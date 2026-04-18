"""{FUNCTION} specific tests — Layer 3.

REPLACE this file with tests for your specific tools.
This template shows the pattern.

Every tool test must:
- Test happy path (valid input → valid output)
- Test error path (invalid input → error status)
- Test edge cases (empty input, large input, etc.)
"""

import pytest
from src.models.schemas import TemplateInput, TemplateOutput


class TestTemplateInput:
    """Input model validation."""

    def test_valid_input(self):
        inp = TemplateInput(query="test query")
        assert inp.query == "test query"
        assert inp.options is None

    def test_input_with_options(self):
        inp = TemplateInput(query="test", options={"key": "value"})
        assert inp.options == {"key": "value"}

    def test_input_requires_query(self):
        with pytest.raises(Exception):
            TemplateInput()  # Missing required field


class TestTemplateOutput:
    """Output model validation."""

    def test_success_output(self):
        out = TemplateOutput(status="ok", data={"result": "value"})
        assert out.status == "ok"
        assert out.data == {"result": "value"}
        assert out.error is None

    def test_error_output(self):
        out = TemplateOutput(status="error", error="Something went wrong")
        assert out.status == "error"
        assert out.error == "Something went wrong"
        assert out.data is None
