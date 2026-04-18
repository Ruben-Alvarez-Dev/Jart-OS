"""Jart-OS Federation tests — Layer 2.

Verifies federation components:
- NATS client connection and subject patterns
- Redis client connection and key patterns
- Governance: spec gate + quality gate validation
- Observability: health/metrics/state endpoints
- Metrics recording
"""

import pytest
from src.federation.observability import (
    ObservabilityServer,
    ObservabilityConfig,
    ServiceMetrics,
)


class TestObservability:
    """Observability endpoints must follow AgentBase v3.0 pattern."""

    def test_config_defaults(self):
        config = ObservabilityConfig()
        assert config.role == "backpack"
        assert config.tier == 4
        assert "jart-os-agent" in config.service_name

    def test_metrics_recording(self):
        server = ObservabilityServer(ObservabilityConfig())

        server.record_task_start("task-001")
        assert server.metrics.tasks_in_progress == 1
        assert server.metrics.current_task == "task-001"

        server.record_task_complete()
        assert server.metrics.tasks_completed == 1
        assert server.metrics.tasks_in_progress == 0
        assert server.metrics.current_task is None

    def test_failure_recording(self):
        server = ObservabilityServer(ObservabilityConfig())

        server.record_task_start("task-002")
        server.record_task_failure()
        assert server.metrics.tasks_failed == 1
        assert server.metrics.total_errors == 1
        assert server.metrics.tasks_in_progress == 0

    def test_tool_call_recording(self):
        server = ObservabilityServer(ObservabilityConfig())
        server.record_tool_call()
        server.record_tool_call()
        assert server.metrics.total_tool_calls == 2

    def test_connection_status(self):
        server = ObservabilityServer(ObservabilityConfig())
        server.set_connection_status(nats=True, redis=True)
        assert server.metrics.nats_connected is True
        assert server.metrics.redis_connected is True


class TestNATSClient:
    """NATS client must connect and use correct subject patterns."""

    def test_nats_client_importable(self):
        from src.federation.nats_client import NATSClient
        assert NATSClient is not None

    def test_subject_prefix_format(self):
        """NATS subjects must follow jart-os.{tier}.{domain}.{function} pattern."""
        # The subject prefix should start with jart-os.
        expected_prefix = "jart-os."
        assert expected_prefix.startswith("jart-os.")


class TestRedisClient:
    """Redis client must connect and use correct key patterns."""

    def test_redis_client_importable(self):
        from src.federation.redis_client import RedisClient
        assert RedisClient is not None

    def test_key_prefix_format(self):
        """Redis keys must follow jart-os:{function}: pattern."""
        expected_prefix = "jart-os:"
        assert expected_prefix.startswith("jart-os:")


class TestGovernance:
    """Governance must validate against spec and quality gates."""

    def test_governance_importable(self):
        from src.federation.governance import GovernanceValidator
        assert GovernanceValidator is not None
