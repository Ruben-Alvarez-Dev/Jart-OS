"""
Jart-OS Guardian Agent — Policy Gate Validator
Validates specs pre-execution and outputs post-execution.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "agents"))

from core.base import AgentBase


class GuardianAgent(AgentBase):
    def __init__(self):
        super().__init__(role="guardian", domain="study", tier=4)

    def run(self):
        """Main loop: validate submissions."""
        self.log.info("Guardian running. Watching for checks...")
        self.notify_discord("🛡️ Guardian ready — watching for checks")
        
        while True:
            try:
                check = self.get_state("guardian:pending_check")
                if check:
                    self.validate(check)
                    self.set_state("guardian:pending_check", {})
                time.sleep(1)
            except KeyboardInterrupt:
                self.log.info("Guardian shutting down")
                break

    def validate(self, submission: dict):
        """Validate output against quality gate thresholds."""
        task_id = submission.get("task_id", "UNKNOWN")
        payload = submission.get("payload", {})
        output = payload.get("output", "")
        spec = payload.get("spec", {})
        retry_count = submission.get("retry_count", 0)
        max_retries = submission.get("max_retries", 3)
        
        self.log.info(f"Validating {task_id} (attempt {retry_count + 1}/{max_retries})")
        self.current_task = task_id
        
        # Use LLM to evaluate against criteria
        criteria = spec.get("success_criteria", [
            "Output addresses the objective",
            "Content is factually accurate",
            "Format is appropriate",
        ])
        
        evaluation = self.call_llm(
            model="qwen25-guardian",
            messages=[
                {"role": "system", "content": "You are a strict quality validator. Score each criterion 0-1. Return JSON: {scores: {criterion: score}, verdict: PASS or FAIL, reason: string}"},
                {"role": "user", "content": f"Criteria: {criteria}\n\nOutput to validate:\n{output[:2000]}"},
            ],
            temperature=0.1,
            max_tokens=512,
        )
        
        content = self.extract_content(evaluation)
        
        # Determine verdict
        is_pass = "PASS" in content.upper() and "FAIL" not in content.upper()
        overall_score = 0.85 if is_pass else 0.45  # Simplified scoring
        
        verdict = {
            "task_id": task_id,
            "verdict": "PASS" if is_pass else "FAIL",
            "overall_score": overall_score,
            "retry_count": retry_count + 1,
            "evaluation": content[:500],
        }
        
        # Publish verdict
        self.publish("jart-os.04.study.guardian.verdicts", verdict)
        
        if is_pass:
            self.log.info(f"✅ {task_id}: PASS (score {overall_score})")
            self.tasks_completed += 1
            self.notify_discord(f"✅ PASS: {task_id}")
        else:
            self.log.warning(f"❌ {task_id}: FAIL (attempt {retry_count + 1})")
            self.tasks_failed += 1
            
            if retry_count + 1 >= max_retries:
                # Escalate to council
                self.publish("jart-os.04.study.council.escalation", verdict)
                self.log.warning(f"🚨 {task_id} escalated to Council (max retries)")
                self.notify_discord(f"🚨 ESCALATED: {task_id} → Council")
            else:
                self.notify_discord(f"❌ FAIL: {task_id} (retry {retry_count + 1}/{max_retries})")
        
        self.current_task = None


import time
if __name__ == "__main__":
    agent = GuardianAgent()
    agent.boot()
