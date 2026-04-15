"""
Jart-OS Study Domain Agent
Spec: §18 "Study Domain — 5 Blocks"
     §15 "Domain Map"
     §17 "Tri-Unit Pattern"
"""

import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from agents.core.base import AgentBase

log = logging.getLogger("jart-os.study.domain")


class StudyDomainAgent(AgentBase):
    """
    Study Domain Agent - Coordinates all study-related operations.
    Manages the 5 study blocks and integrates with existing agents.
    — §18 "Study Domain — 5 Blocks"
    """
    
    def __init__(self):
        super().__init__(role="study_domain", domain="study", tier=4)
        self.study_path = Path("$JART_OS_HOME/study")
        self.config_path = self.study_path / "config/study_domain.yaml"
        self.config = None
        self.current_block = None
        
    def boot(self):
        """Override boot to load study configuration."""
        super().boot()
        self.load_study_config()
        log.info("Study Domain Agent booted successfully")
        
    def load_study_config(self):
        """Load study domain configuration."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            log.info(f"Study config loaded: {len(self.config.get('blocks', {}))} blocks")
            return True
        except Exception as e:
            log.error(f"Failed to load study config: {e}")
            return False
    
    def get_block_status(self, block_name: str) -> dict:
        """Get status of a specific study block."""
        block_path = self.study_path / block_name
        metadata_path = block_path / "metadata.json"
        
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to load block metadata: {e}")
            return {"status": "error", "error": str(e)}
    
    def update_block_status(self, block_name: str, status: str, services: list = None):
        """Update status of a study block."""
        block_path = self.study_path / block_name
        metadata_path = block_path / "metadata.json"
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata["status"] = status
            metadata["updated_at"] = datetime.now().isoformat()
            if services:
                metadata["services"] = services
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            log.info(f"Block {block_name} status updated to {status}")
            return True
        except Exception as e:
            log.error(f"Failed to update block status: {e}")
            return False
    
    def get_topics_progress(self) -> dict:
        """Get progress on topics."""
        topics_path = self.study_path / "topics"
        index_path = topics_path / "index.json"
        
        try:
            with open(index_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to load topics index: {e}")
            return {}
    
    def create_study_task(self, block: str, task_type: str, params: dict) -> dict:
        """Create a new study task."""
        task_id = f"{block}_{task_type}_{int(time.time())}"
        
        task = {
            "task_id": task_id,
            "block": block,
            "task_type": task_type,
            "params": params,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "assigned_to": None
        }
        
        # Save task to block's data directory
        task_path = self.study_path / block / "data" / f"{task_id}.json"
        with open(task_path, 'w') as f:
            json.dump(task, f, indent=2)
        
        log.info(f"Study task created: {task_id}")
        
        # Publish task creation event
        self.publish(self.subject_events, {
            "event": "study_task_created",
            "task_id": task_id,
            "block": block,
            "task_type": task_type
        })
        
        return task
    
    def run(self):
        """Main loop: coordinate study domain operations."""
        self.log.info("Study Domain Agent running. Waiting for commands...")

        async def on_command(msg):
            try:
                data = json.loads(msg.data.decode())
                action = data.get("action", "status")

                if action == "status":
                    # Return overall study domain status
                    status = {
                        "domain": "study",
                        "blocks": {block: self.get_block_status(block) 
                                  for block in ["syllabus", "theoretical", "practical", "oral"]},
                        "topics": self.get_topics_progress(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.publish(self.subject_events, {
                        "event": "study_status",
                        "status": status
                    })

                elif action == "create_task":
                    block = data.get("block")
                    task_type = data.get("task_type")
                    params = data.get("params", {})
                    
                    task = self.create_study_task(block, task_type, params)
                    
                    self.publish(self.subject_events, {
                        "event": "study_task_response",
                        "task": task
                    })

                elif action == "update_block":
                    block = data.get("block")
                    status = data.get("status")
                    services = data.get("services")
                    
                    success = self.update_block_status(block, status, services)
                    
                    self.publish(self.subject_events, {
                        "event": "block_updated",
                        "block": block,
                        "success": success
                    })

            except Exception as e:
                self.log.error(f"Study domain agent error: {e}")
                self.tasks_failed += 1

        # Subscribe to study.domain.command — §12
        if self._loop:
            self._loop.run_until_complete(
                self.nats_subscribe(self.subject_command, on_command)
            )

        # Keep alive
        while self._running:
            self.redis_heartbeat()
            time.sleep(10)


def main():
    """Entry point for Study Domain Agent."""
    agent = StudyDomainAgent()
    agent.boot()


if __name__ == "__main__":
    main()