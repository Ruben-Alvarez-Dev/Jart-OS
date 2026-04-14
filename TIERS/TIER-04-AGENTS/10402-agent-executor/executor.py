"""
Jart-OS Executor Agent — Study Domain
Executes specs, generates content, submits to Guardian for validation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "agents"))

from core.base import AgentBase


class ExecutorAgent(AgentBase):
    def __init__(self):
        super().__init__(role="executor", domain="study", tier=4)

    def run(self):
        """Main loop: execute subtasks, submit for validation."""
        self.log.info("Executor running. Waiting for specs...")
        self.notify_discord("⚡ Executor ready — waiting for specs")
        
        while True:
            try:
                cmd = self.get_state("executor:pending_spec")
                if cmd:
                    self.log.info(f"Executing spec: {cmd.get(\"task_id\")}")
                    self.execute_subtask(cmd)
                    self.set_state("executor:pending_spec", {})
                time.sleep(1)
            except KeyboardInterrupt:
                self.log.info("Executor shutting down")
                break

    def execute_subtask(self, spec: dict):
        """Execute a single subtask spec and submit result to Guardian."""
        task_id = spec.get("task_id", "UNKNOWN")
        objective = spec.get("objective", "")
        model_hint = spec.get("model_hint", "glm-4.7")
        self.current_task = task_id
        
        self.log.info(f"Executing {task_id}: {objective[:80]}")
        
        # Execute via LLM
        result = self.call_llm(
            model=model_hint,
            messages=[
                {"role": "system", "content": "You are an expert content creator for competitive exam preparation (domain subject). Be precise, factual, and thorough."},
                {"role": "user", "content": objective},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        
        content = self.extract_content(result)
        
        # Submit to Guardian for validation
        self.publish(
            "jart-os.04.study.guardian.checks",
            self.make_envelope(
                task_id=task_id,
                objective=f"Validate output for: {objective}",
                payload={"output": content, "spec": spec},
            ),
        )
        
        self.log.info(f"Submitted {task_id} to Guardian ({len(content)} chars)")
        self.tasks_completed += 1
        self.current_task = None


import time
if __name__ == "__main__":
    agent = ExecutorAgent()
    agent.boot()
