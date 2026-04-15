#!/usr/bin/env python3
"""
Jart-OS — Integration Test for Tri-Unit Flow
Spec: §11 'Flow: Task Lifecycle' steps 1-7
     §14 'Policy Gates & Governance'
     §12 'Communication Backbone (NATS)'
"""

import asyncio
import json
import time
import sys
sys.path.insert(0, "..")

from core.base import AgentBase

log = logging.getLogger("jart-os.test")


class TestDirector(AgentBase):
    """Test Director: publishes task to executor."""

    def run(self):
        self.log.info("Test Director: publishing test task...")
        task = self.build_envelope(
            objective="Generate summary for topic 3",
            spec={"topic": 3, "domain": "study"},
            success_criteria=["summary_complete", "accurate"],
            model_hint="glm-4.7",
        )
        task["to"] = f"executor-{self.domain}"
        self.publish(self.domain_subject("executor", "command"), task)
        self.log.info("Test Director: task published")
        time.sleep(2)
        self.boot()  # Keep alive


class TestExecutor(AgentBase):
    """Test Executor: receives task, executes, sends to guardian."""

    def run(self):
        self.log.info("Test Executor: waiting for commands...")

        async def on_command(msg):
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id")
                self.log.info(f"Test Executor: received {task_id}")

                # Execute via LLM
                result = self.call_llm_text(
                    model="glm-4.7",
                    prompt=f"Generate a brief summary for topic 3.",
                    system="You are a test executor. Keep it short.",
                    temperature=0.3,
                )

                # Send to guardian
                self.publish(self.domain_subject("guardian", "checks"), {
                    "task_id": task_id,
                    "result": result,
                    "from": f"executor-{self.domain}",
                    "original_task": data,
                })
                self.tasks_completed += 1
                self.log.info(f"Test Executor: sent to guardian")

            except Exception as e:
                self.log.error(f"Test Executor error: {e}")
                self.tasks_failed += 1

        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(1)


class TestGuardian(AgentBase):
    """Test Guardian: validates, returns verdict."""

    def run(self):
        self.log.info("Test Guardian: waiting for checks...")

        async def on_check(msg):
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id")
                result = data.get("result", "")
                self.log.info(f"Test Guardian: checking {task_id}")

                # Validate via LLM
                verdict = self.call_llm_text(
                    model="phi3-local",
                    prompt=(
                        f"Validate this output. Is it complete and accurate?\n\n"
                        f"Output: {result}\n\n"
                        f"Reply ONLY with JSON: {{\"verdict\": \"PASS\" or \"FAIL\", "
                        f"\"reason\": \"...\"}}"
                    ),
                    system="You are a strict validator.",
                    temperature=0.1,
                )

                # Parse verdict
                passed = "PASS" in verdict.upper()
                self.publish(self.domain_subject("guardian", "verdicts"), {
                    "task_id": task_id,
                    "verdict": "PASS" if passed else "FAIL",
                    "reason": verdict,
                    "from": f"guardian-{self.domain}",
                    "original_task": data.get("original_task", {}),
                })

                if passed:
                    self.tasks_completed += 1
                else:
                    self.tasks_failed += 1

            except Exception as e:
                self.log.error(f"Test Guardian error: {e}")

        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(
                    self.subject_command.replace("command", "checks"),
                    on_check,
                )
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(1)


class TestCouncil(AgentBase):
    """Test Council: votes on proposals."""

    def run(self):
        self.log.info("Test Council: waiting for proposals...")

        async def on_proposal(msg):
            try:
                data = json.loads(msg.data.decode())
                task_id = data.get("task_id")
                self.log.info(f"Test Council: received proposal {task_id}")

                # 3 reviewers: Legal, Pedagogical, Technical
                reviewers = [
                    {
                        "name": "legal",
                        "model": "glm-5",
                        "prompt": "Review for regulatory compliance. APPROVE or REJECT with reason.",
                    },
                    {
                        "name": "pedagogical",
                        "model": "glm-4.7",
                        "prompt": "Review for pedagogical quality. APPROVE or REJECT with reason.",
                    },
                    {
                        "name": "technical",
                        "model": "phi3-local",
                        "prompt": "Review for technical accuracy. APPROVE or REJECT with reason.",
                    },
                ]

                votes = {}
                for reviewer in reviewers:
                    vote_text = self.call_llm_text(
                        model=reviewer["model"],
                        prompt=(
                            f"{reviewer['prompt']}\n\n"
                            f"Content to review:\n{data.get('result', '')}\n\n"
                            f"Reply ONLY: APPROVE or REJECT with brief reason."
                        ),
                        temperature=0.2,
                    )
                    votes[reviewer["name"]] = "APPROVE" if "APPROVE" in vote_text.upper() else "REJECT"

                # Consensus: 66% (2/3) for normal, 100% for critical
                is_critical = data.get("priority") == "critical"
                threshold = 3 if is_critical else 2
                consensus = "APPROVED" if sum(1 for v in votes.values() if v == "APPROVE") >= threshold else "REJECTED"

                self.publish(self.domain_subject("council", "votes"), {
                    "task_id": task_id,
                    "consensus": consensus,
                    "votes": votes,
                    "approves": sum(1 for v in votes.values() if v == "APPROVE"),
                    "threshold": threshold,
                    "is_critical": is_critical,
                })

                self.tasks_completed += 1
                self.log.info(f"Test Council: voted {consensus}")

            except Exception as e:
                self.log.error(f"Test Council error: {e}")

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
            time.sleep(1)


async def run_test():
    """Run full tri-unit test: Director → Executor → Guardian → Council."""
    log.info("=== Starting Jart-OS Tri-Unit Integration Test ===")

    # Start all test agents
    director = TestDirector()
    executor = TestExecutor()
    guardian = TestGuardian()
    council = TestCouncil()

    # Start in background
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(lambda: director.boot()),
            executor.submit(lambda: executor.boot()),
            executor.submit(lambda: guardian.boot()),
            executor.submit(lambda: council.boot()),
        ]

        # Wait for Director to publish
        log.info("Waiting 5 seconds for Director to publish task...")
        await asyncio.sleep(5)

        # Check results
        log.info("Checking test results...")
        time.sleep(3)

        # Stop all agents
        director._running = False
        executor._running = False
        guardian._running = False
        council._running = False

        # Report
        log.info("=== Test Complete ===")
        log.info(f"Director tasks: {director.tasks_completed}")
        log.info(f"Executor tasks: {executor.tasks_completed}")
        log.info(f"Guardian tasks: {guardian.tasks_completed}")
        log.info(f"Council tasks: {council.tasks_completed}")


if __name__ == "__main__":
    asyncio.run(run_test())
