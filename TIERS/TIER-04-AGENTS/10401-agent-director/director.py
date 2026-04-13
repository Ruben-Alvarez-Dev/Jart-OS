"""
Jart-OS Director Agent — Oposiciones Domain
Receives tasks, plans, decomposes, delegates, assembles.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "agents"))

from core.base import AgentBase


class DirectorAgent(AgentBase):
    def __init__(self):
        super().__init__(role="director", domain="oposiciones", tier=4)

    def run(self):
        """Main loop: listen for commands, plan, delegate."""
        self.log.info("Director running. Waiting for tasks...")
        self.notify_discord("📋 Director ready — waiting for tasks")
        
        # TODO: Subscribe to NATS command subject
        # For now, simple poll loop
        while True:
            try:
                # Check for commands in Redis (interim until full NATS subscription)
                cmd = self.get_state("director:pending_command")
                if cmd:
                    self.log.info(f"Received command: {cmd.get(\"task_id\")}")
                    self.process_command(cmd)
                    self.set_state("director:pending_command", {})
                
                time.sleep(1)
            except KeyboardInterrupt:
                self.log.info("Director shutting down")
                break

    def process_command(self, command: dict):
        """Process incoming command: plan and delegate."""
        task_id = command.get("task_id", "UNKNOWN")
        objective = command.get("objective", "")
        self.current_task = task_id
        
        self.log.info(f"Planning task {task_id}: {objective[:80]}")
        
        # 1. Ask LLM to decompose the task
        decomposition = self.call_llm(
            model="qwen25-director",
            messages=[
                {"role": "system", "content": "You are a task planner for Spanish civil service exam preparation. Decompose the given objective into concrete subtasks. Return JSON with keys: subtasks (list of {id, objective, model_hint, success_criteria})."},
                {"role": "user", "content": f"Task: {objective}\nDomain: oposiciones / hostelería"},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        
        # 2. Delegate each subtask to executor
        content = self.extract_content(decomposition)
        self.log.info(f"Plan generated ({len(content)} chars)")
        
        # 3. Publish event
        self.publish(
            "jart-os.04.oposiciones.director.events",
            self.make_envelope(task_id, "Task decomposed and delegated", {"plan": content}),
        )
        
        self.tasks_completed += 1
        self.current_task = None
        self.notify_discord(f"✅ Task {task_id} planned and delegated")


import time
if __name__ == "__main__":
    agent = DirectorAgent()
    agent.boot()
