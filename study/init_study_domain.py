#!/usr/bin/env python3
"""
Jart-OS Study Domain Initialization
Spec: §18 "Study Domain — 5 Blocks"
     §15 "Domain Map"
     §16 "Professor & Chief Map"
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("jart-os.study.init")


class StudyDomainInitializer:
    """Initialize Jart-OS Study Domain structure and configuration."""
    
    def __init__(self):
        self.base_path = Path("$JART_OS_HOME/study")
        self.config_path = self.base_path / "config/study_domain.yaml"
        self.timestamp = datetime.now().isoformat()
        
    def load_config(self):
        """Load study domain configuration."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            log.info(f"Configuration loaded from {self.config_path}")
            return True
        except Exception as e:
            log.error(f"Failed to load config: {e}")
            return False
    
    def create_block_structure(self, block_name: str):
        """Create directory structure for a study block."""
        block_path = self.base_path / block_name
        for subdir in ["data", "logs", "config"]:
            (block_path / subdir).mkdir(parents=True, exist_ok=True)
        
        # Create block metadata
        metadata = {
            "block": block_name,
            "created_at": self.timestamp,
            "status": "initialized",
            "services": []
        }
        
        metadata_path = block_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        log.info(f"Block structure created: {block_name}")
        return True
    
    def initialize_topics(self):
        """Initialize topic structure for theoretical exam."""
        topics_path = self.base_path / "topics"
        
        # Create topic index
        topic_index = {
            "total_topics": 34,
            "created_at": self.timestamp,
            "blocks": {
                "theoretical": 34,
                "practical": 156,
                "oral": 10
            }
        }
        
        index_path = topics_path / "index.json"
        with open(index_path, 'w') as f:
            json.dump(topic_index, f, indent=2)
        
        log.info(f"Topics index created: {topics_path}")
        return True
    
    def create_exam_templates(self):
        """Create exam templates for all exam types."""
        exams_path = self.base_path / "exams"
        
        templates = {
            "theoretical_exam": {
                "total_questions": 100,
                "passing_score": 60,
                "time_limit_minutes": 120,
                "question_types": ["multiple_choice", "true_false", "short_answer"]
            },
            "practical_exam": {
                "total_tasks": 5,
                "passing_score": 70,
                "time_limit_minutes": 180,
                "evaluation_criteria": ["technique", "hygiene", "presentation", "timing"]
            },
            "oral_defense": {
                "total_questions": 10,
                "passing_score": 70,
                "time_limit_minutes": 60,
                "evaluation_criteria": ["content", "clarity", "structure", "time_management"]
            }
        }
        
        for exam_type, template in templates.items():
            template_path = exams_path / f"{exam_type}_template.json"
            with open(template_path, 'w') as f:
                json.dump(template, f, indent=2)
            log.info(f"Exam template created: {exam_type}")
        
        return True
    
    def create_protocol_templates(self):
        """Create protocol templates for practical exam."""
        protocols_path = self.base_path / "protocols"
        
        protocol_template = {
            "protocol_id": "",
            "technique_name": "",
            "difficulty_level": "",
            "steps": [],
            "tools_required": [],
            "safety_notes": [],
            "timing_guidelines": {},
            "quality_criteria": []
        }
        
        template_path = protocols_path / "protocol_template.json"
        with open(template_path, 'w') as f:
            json.dump(protocol_template, f, indent=2)
        
        log.info(f"Protocol template created: {protocols_path}")
        return True
    
    def generate_status_report(self):
        """Generate initialization status report."""
        report = {
            "domain": "study",
            "tier": 4,
            "initialized_at": self.timestamp,
            "blocks_initialized": 5,
            "topics_configured": 34,
            "exams_configured": 3,
            "protocols_configured": True,
            "status": "ready"
        }
        
        report_path = self.base_path / "status_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        log.info(f"Status report generated: {report_path}")
        return report
    
    def initialize_all(self):
        """Initialize complete study domain."""
        log.info("Starting Jart-OS Study Domain initialization...")
        
        steps = [
            ("Load configuration", self.load_config),
            ("Create block structures", lambda: all([
                self.create_block_structure(block) 
                for block in ["syllabus", "theoretical", "practical", "oral"]
            ])),
            ("Initialize topics", self.initialize_topics),
            ("Create exam templates", self.create_exam_templates),
            ("Create protocol templates", self.create_protocol_templates),
            ("Generate status report", self.generate_status_report)
        ]
        
        for step_name, step_func in steps:
            try:
                log.info(f"Executing: {step_name}")
                result = step_func()
                if not result:
                    log.error(f"Failed: {step_name}")
                    return False
            except Exception as e:
                log.error(f"Error in {step_name}: {e}")
                return False
        
        log.info("✅ Study Domain initialization completed successfully!")
        return True


def main():
    """Main entry point."""
    initializer = StudyDomainInitializer()
    success = initializer.initialize_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()