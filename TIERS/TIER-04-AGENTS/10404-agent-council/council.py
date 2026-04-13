"""
Jart-OS Council Agent — Voting Consensus
Three perspectives: Legal, Pedagogical, Technical.
66% for normal tasks, 100% for critical.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "agents"))

from core.base import AgentBase


class CouncilAgent(AgentBase):
    
    PERSPECTIVES = [
        {"name": "legal", "model": "qwen25-council", "focus": "Normativa LOE/FP/BOJA compliance"},
        {"name": "pedagogical", "model": "qwen25-council", "focus": "Resultados de aprendizaje y criterios de evaluacion"},
        {"name": "technical", "model": "qwen25-council", "focus": "Exactitud tecnica del contenido de hosteleria"},
    ]

    def __init__(self):
        super().__init__(role="council", domain="oposiciones", tier=4)

    def run(self):
        """Main loop: review escalations and vote."""
        self.log.info("Council running. Watching for escalations...")
        self.notify_discord("🏛️ Council ready — 3 perspectives active")
        
        while True:
            try:
                escalation = self.get_state("council:pending_escalation")
                if escalation:
                    self.review(escalation)
                    self.set_state("council:pending_escalation", {})
                time.sleep(1)
            except KeyboardInterrupt:
                self.log.info("Council shutting down")
                break

    def review(self, escalation: dict):
        """Run 3-perspective vote on escalated task."""
        task_id = escalation.get("task_id", "UNKNOWN")
        output = escalation.get("payload", {}).get("output", "")
        is_critical = escalation.get("priority", "normal") == "critical"
        threshold = 1.0 if is_critical else 0.66
        
        self.log.info(f"Reviewing {task_id} (critical={is_critical}, threshold={threshold})")
        self.current_task = task_id
        
        votes = []
        for p in self.PERSPECTIVES:
            vote_result = self.call_llm(
                model=p["model"],
                messages=[
                    {"role": "system", "content": f"You are a {p[\"name\"]} reviewer for Spanish civil service exam content. Focus on: {p[\"focus\"]}. Vote APPROVE or REJECT with reason."},
                    {"role": "user", "content": f"Review this content and vote:\n\n{output[:3000]}"},
                ],
                temperature=0.2,
                max_tokens=256,
            )
            vote_text = self.extract_content(vote_result)
            approved = "APPROVE" in vote_text.upper()
            votes.append({
                "perspective": p["name"],
                "approved": approved,
                "reasoning": vote_text[:300],
            })
            self.log.info(f"  {p[\"name\"]}: {✅
