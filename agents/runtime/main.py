"""
Jart-OS Agent Runtime v3.0 — NATS-only
=======================================
Spec references:
  §11 — Agent Architecture (Tri-Unit roles, Task Lifecycle)
  §12 — Communication Backbone (NATS subjects)
  §24 D3 — NATS JetStream for ALL messaging (NOT Redis PubSub)
  §10 — LLM Routing Strategy (Model→Role Mapping)
  §14 — Policy Gates (Council, Consensus)

All 4 agent roles inherit from AgentBase.
ZERO Redis PubSub usage. All messaging via NATS.
"""

import os
import sys
import json
import time
import asyncio
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.base import AgentBase

log = logging.getLogger("jart-os.runtime")


# =================================================================
# Director Agent — §11 'Director: Plans, Decomposes, Delegates'
#                  §10 'Director (plan): glm-5, temp 0.7'
# =================================================================

class StudyDirector(AgentBase):
    """
    Director agent for study domain.
    Plans tasks, decomposes into sub-tasks, delegates to executor.
    — §11 'Flow: Task Lifecycle' steps 1-2, 6-7
    """

    def __init__(self):
        super().__init__(role="director", domain="study", tier=4)
        self.model = os.getenv("DIRECTOR_MODEL", "glm-5")  # §10
        self.temperature = 0.7  # §10 'Director (plan): temp 0.7'

    def run(self):
        """Main loop: subscribe to commands, plan, delegate. — §11 step 1-2"""
        self.log.info("Director running. Waiting for commands...")

        async def on_command(msg):
            """Handle incoming command. — §11 step 1"""
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id", "unknown")
                self.log.info(f"Received command: {task_id}")
                self.current_task = task_id

                # Plan decomposition using LLM — §11 step 2
                plan = self.call_llm_text(
                    model=self.model,
                    prompt=f"Decompose this task into sub-tasks:\n{json.dumps(data, indent=2)}",
                    system="You are a task planner. Return a JSON array of sub-tasks.",
                    temperature=self.temperature,
                )

                # Publish sub-tasks to executor — §11 step 2
                envelope = self.build_envelope(
                    objective=f"Execute sub-tasks for {task_id}",
                    context={"original_task": data, "plan": plan},
                )
                envelope["to"] = f"executor-{self.domain}"
                self.publish(self.domain_subject("executor", "command"), envelope)

                # Log completion
                self.tasks_completed += 1
                self.current_task = None
                self.publish(self.subject_events, {
                    "event": "task_delegated",
                    "task_id": task_id,
                    "sub_tasks_count": 1,
                })

            except Exception as e:
                self.log.error(f"Command handler error: {e}")
                self.tasks_failed += 1

        # Subscribe to director.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)


# =================================================================
# Executor Agent — §11 'Executor: Executes, Generates, Reports'
#                  §10 'Executor (code): glm-4.7, temp 0.3'
# =================================================================

class StudyExecutor(AgentBase):
    """
    Executor agent for study domain.
    Receives sub-tasks, executes via LLM, sends to guardian.
    — §11 'Flow: Task Lifecycle' steps 3, 5
    """

    def __init__(self):
        super().__init__(role="executor", domain="study", tier=4)
        self.model = os.getenv("EXECUTOR_MODEL", "glm-4.7")  # §10
        self.temperature = 0.3  # §10 'Executor (code): temp 0.3'

    def run(self):
        """Main loop: execute sub-tasks, send to guardian. — §11 step 3"""
        self.log.info("Executor running. Waiting for sub-tasks...")

        async def on_command(msg):
            """Handle incoming sub-task. — §11 step 3"""
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id", "unknown")
                self.current_task = task_id
                self.log.info(f"Executing: {task_id}")

                # Execute via LLM — §11 'Executor: Executes, Generates'
                objective = data.get("payload", {}).get("objective", "")
                result = self.call_llm_text(
                    model=self.model,
                    prompt=f"Execute this task:\n{objective}",
                    system="You are a precise task executor. Follow instructions exactly.",
                    temperature=self.temperature,
                )

                # Send to guardian for validation — §11 step 3
                self.publish(self.domain_subject("guardian", "checks"), {
                    "task_id": task_id,
                    "from": f"executor-{self.domain}",
                    "result": result,
                    "original_task": data,
                    "retry_count": data.get("retry_count", 0),
                })

                self.tasks_completed += 1
                self.current_task = None

            except Exception as e:
                self.log.error(f"Executor error: {e}")
                self.tasks_failed += 1
                self.publish(self.subject_errors, {
                    "task_id": task_id if 'task_id' in dir() else "unknown",
                    "error": str(e),
                })

        # Subscribe to executor.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)


# =================================================================
# Guardian Agent — §11 'Guardian: Validates, Verifies, Approves/Rejects'
#                  §10 'Guardian (validate): mimo-flash/phi3-local, temp 0.1'
# =================================================================

class StudyGuardian(AgentBase):
    """
    Guardian agent for study domain.
    Validates executor output against quality gates.
    — §11 'Flow: Task Lifecycle' step 4
    — §14 'Policy Gates & Governance'
    """

    def __init__(self):
        super().__init__(role="guardian", domain="study", tier=4)
        self.model = os.getenv("GUARDIAN_MODEL", "phi3-local")  # §10
        self.temperature = 0.1  # §10 'Guardian: temp 0.1'

    def run(self):
        """Main loop: validate results, return verdict. — §11 step 4"""
        self.log.info("Guardian running. Waiting for checks...")

        async def on_check(msg):
            """Validate executor output. — §11 step 4, §14 Layer B"""
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id", "unknown")
                result = data.get("result", "")
                self.current_task = task_id

                # Validate via LLM — §14 Layer B
                verdict = self.call_llm_text(
                    model=self.model,
                    prompt=(
                        f"Validate this output. Is it complete, accurate, and well-formatted?\n\n"
                        f"Output:\n{result}\n\n"
                        f"Reply ONLY with JSON: {{\"verdict\": \"PASS\" or \"FAIL\", "
                        f"\"reason\": \"...\", \"completeness\": 0.0-1.0, "
                        f"\"accuracy\": 0.0-1.0, \"format\": 0.0-1.0}}"
                    ),
                    system="You are a strict quality validator. Be thorough.",
                    temperature=self.temperature,
                )

                # Parse verdict
                passed = "PASS" in verdict.upper()
                retry_count = data.get("retry_count", 0)

                # Publish verdict — §11 step 4
                self.publish(self.domain_subject("guardian", "verdicts"), {
                    "task_id": task_id,
                    "verdict": "PASS" if passed else "FAIL",
                    "reason": verdict,
                    "retry_count": retry_count,
                    "original_task": data.get("original_task", {}),
                    "result": result,
                })

                # Audit trail — §14 Layer C
                self.audit_log(task_id, {
                    "action": "guardian_check",
                    "verdict": "PASS" if passed else "FAIL",
                    "retry_count": retry_count,
                })

                if passed:
                    self.tasks_completed += 1
                else:
                    self.tasks_failed += 1

                self.current_task = None

            except Exception as e:
                self.log.error(f"Guardian error: {e}")
                self.tasks_failed += 1

        # Subscribe to guardian.checks — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command.replace("command", "checks"), on_check)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)


# =================================================================
# Council Agent — §14 'Council (Tri-Unit Review)'
#                 §10 'Council (vote): 3 different models, temp 0.2'
# =================================================================

class StudyCouncil(AgentBase):
    """
    Council agent for study domain.
    3-aspect review: Legal, Pedagogical, Technical.
    — §14 'Council Tri-Unit Review' table
    — §14 'Consensus Rules'
    """

    def __init__(self):
        super().__init__(role="council", domain="study", tier=4)
        self.temperature = 0.2  # §10 'Council: temp 0.2'

    def run(self):
        """Main loop: vote on proposals. — §14"""
        self.log.info("Council running. Waiting for proposals...")

        async def on_proposal(msg):
            """Vote on a proposal. — §14 Consensus Rules"""
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id", "unknown")
                self.current_task = task_id

                # 3 reviewers — §14 'Council Tri-Unit Review'
                reviewers = [
                    {
                        "name": "legal",
                        "model": os.getenv("COUNCIL_MODEL_1", "glm-5"),
                        "prompt": (
                            "Review for regulatory compliance (LOE/FP/regulatory framework). "
                            "Reject if missing regulation reference. — §14 Legal reviewer"
                        ),
                    },
                    {
                        "name": "pedagogical",
                        "model": os.getenv("COUNCIL_MODEL_2", "glm-4.7"),
                        "prompt": (
                            "Review for pedagogical quality (RA/CE alignment). "
                            "Reject if misaligned curriculum. — §14 Pedagogical reviewer"
                        ),
                    },
                    {
                        "name": "technical",
                        "model": os.getenv("COUNCIL_MODEL_3", "phi3-local"),
                        "prompt": (
                            "Review for technical accuracy (domain subject). "
                            "Reject if factually wrong. — §14 Technical reviewer"
                        ),
                    },
                ]

                votes = {}
                for reviewer in reviewers:
                    vote_text = self.call_llm_text(
                        model=reviewer["model"],
                        prompt=(
                            f"{reviewer['prompt']}\n\n"
                            f"Content to review:\n{data.get('result', '')}\n\n"
                            f"Reply ONLY: APPROVE or REJECT with reason."
                        ),
                        temperature=self.temperature,
                    )
                    votes[reviewer["name"]] = "APPROVE" if "APPROVE" in vote_text.upper() else "REJECT"

                # Consensus — §14 'Normal 66% (2/3), Critical 100% (3/3)'
                approves = sum(1 for v in votes.values() if v == "APPROVE")
                is_critical = data.get("priority") == "critical"
                threshold = 3 if is_critical else 2  # §14
                consensus = "APPROVED" if approves >= threshold else "REJECTED"

                # Publish vote — §12
                self.publish(self.domain_subject("council", "votes"), {
                    "task_id": task_id,
                    "consensus": consensus,
                    "votes": votes,
                    "approves": approves,
                    "threshold": threshold,
                    "is_critical": is_critical,
                })

                # Audit trail — §14 Layer C
                self.audit_log(task_id, {
                    "action": "council_vote",
                    "consensus": consensus,
                    "votes": votes,
                })

                self.tasks_completed += 1
                self.current_task = None

            except Exception as e:
                self.log.error(f"Council error: {e}")
                self.tasks_failed += 1

        # Subscribe to council.proposals — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(
                    self.subject_command.replace("command", "proposals"),
                    on_proposal,
                )
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)


# =================================================================
# Entry point — role-based agent selection
# =================================================================

AGENTS = {
    "director": StudyDirector,
    "executor": StudyExecutor,
    "guardian": StudyGuardian,
    "council": StudyCouncil,
}


def main():
    """Start agent based on AGENT_ROLE env var."""
    role = os.getenv("AGENT_ROLE", "director")
    if role not in AGENTS:
        log.error(f"Unknown role: {role}. Available: {list(AGENTS.keys())}")
        sys.exit(1)

    agent = AGENTS[role]()
    agent.boot()


if __name__ == "__main__":
    main()
