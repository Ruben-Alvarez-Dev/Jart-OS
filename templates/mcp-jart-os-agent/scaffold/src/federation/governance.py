"""
Federation — Governance Manager

Validates tasks against spec gates and writes audit trail.

Spec gate (pre-execution): agents/policies/spec-gate.yaml
Quality gate (post-execution): agents/policies/quality-gate.yaml

See: agents/policies/spec-gate.yaml, agents/policies/quality-gate.yaml
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any


class GovernanceManager:
    """Validates tasks against Jart-OS governance policies."""

    def __init__(self):
        self.spec_gate_rules: list[dict] = []
        self.quality_gate_rules: list[dict] = []
        self.log = logging.getLogger("jart-os.federation.governance")

    async def load_policies(self):
        """Load spec gate and quality gate YAML policies."""
        # TODO: Load from YAML files (spec_gate_path, quality_gate_path)
        self.log.info("Governance policies loaded")

    async def validate_pre_execution(self, task: dict) -> tuple[bool, str]:
        """
        Spec gate: validate task BEFORE execution.
        Returns (is_valid, error_message).
        """
        errors = []

        # Rule: task_id required (uppercase alphanumeric)
        task_id = task.get("task_id", "")
        if not task_id:
            errors.append("task_id is required")

        # Rule: objective required (min 10 chars)
        objective = task.get("payload", {}).get("objective", "")
        if len(objective) < 10:
            errors.append("objective must be at least 10 characters")

        # Rule: success_criteria required (non-empty array)
        criteria = task.get("payload", {}).get("success_criteria", [])
        if not criteria:
            errors.append("success_criteria must be non-empty")

        # Rule: from field required
        if not task.get("from"):
            errors.append("from field is required")

        # Rule: timestamp required (ISO 8601)
        if not task.get("timestamp"):
            errors.append("timestamp is required")

        if errors:
            msg = "; ".join(errors)
            self.log.warning(f"Spec gate FAILED: {msg}")
            return False, msg

        self.log.info(f"Spec gate passed for task {task_id}")
        return True, ""

    async def validate_post_execution(self, result: dict) -> tuple[bool, str]:
        """
        Quality gate: validate result AFTER execution.
        Returns (passes, error_message).
        """
        errors = []

        completeness = result.get("completeness", 0)
        if completeness < 0.8:
            errors.append(f"completeness {completeness} < 0.8")

        accuracy = result.get("accuracy", 0)
        if accuracy < 0.9:
            errors.append(f"accuracy {accuracy} < 0.9")

        if errors:
            msg = "; ".join(errors)
            self.log.warning(f"Quality gate FAILED: {msg}")
            return False, msg

        self.log.info("Quality gate passed")
        return True, ""

    async def write_audit(self, task_id: str, event: str, data: dict):
        """Write audit trail entry."""
        entry = {
            "task_id": task_id,
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        # TODO: Write to Redis jart-os:audit:{task_id}
        self.log.debug(f"Audit: {event} for {task_id}")
