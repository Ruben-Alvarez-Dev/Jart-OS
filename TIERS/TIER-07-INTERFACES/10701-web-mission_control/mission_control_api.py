"""
Jart-OS Mission Control API - Simplified
Spec: §21 "Boot & Operations"
     §22 D8 "Mission Control"
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Flask for HTTP API
from flask import Flask, jsonify, request

log = logging.getLogger("jart-os.mission_control")

app = Flask(__name__)

class MissionControlAPI:
    """Mission Control API - Central interface for Jart-OS management."""
    
    def __init__(self):
        self.base_path = Path("$JART_OS_HOME/Jart-OS")
        self.study_path = self.base_path / "study"
        
    def get_services_status(self) -> Dict[str, Any]:
        """Get status of all Jart-OS services (simplified)."""
        # In production, this would query actual service status
        # For now, return known services
        services = {
            "jart-os-director-study": {"status": "Up", "port": 10401, "role": "Orchestration"},
            "jart-os-executor-study": {"status": "Up", "port": 10402, "role": "Execution"},
            "jart-os-guardian": {"status": "Up", "port": 10403, "role": "Validation"},
            "jart-os-council": {"status": "Up", "port": 10404, "role": "Consensus"},
            "jart-os-study-domain": {"status": "Up", "port": 10500, "role": "Coordination"},
            "jart-os-pipe-pdf": {"status": "Up", "port": 10601, "role": "Content Pipeline"},
            "jart-os-pipe-rag": {"status": "Up", "port": 10604, "role": "RAG Pipeline"},
            "jart-os-litellm": {"status": "Up", "port": 10201, "role": "LLM Gateway"},
            "jart-os-redis": {"status": "Up", "port": 10301, "role": "State Store"},
            "jart-os-nats": {"status": "Up", "port": 10302, "role": "Messaging"},
            "jart-os-mc": {"status": "Up", "port": 10701, "role": "Mission Control"},
            "jart-os-grafana": {"status": "Up", "port": 10702, "role": "Monitoring"},
            "jart-os-prometheus": {"status": "Up", "port": 10901, "role": "Metrics"}
        }
        return services
    
    def get_study_progress(self) -> Dict[str, Any]:
        """Get progress of study domain."""
        try:
            status_path = self.study_path / "status_report.json"
            
            if status_path.exists():
                with open(status_path, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "domain": "study",
                    "status": "initialized",
                    "blocks_initialized": 5,
                    "topics_configured": 34,
                    "exams_configured": 3
                }
                
        except Exception as e:
            log.error(f"Failed to get study progress: {e}")
            return {"error": str(e)}
    
    def get_agents_info(self) -> Dict[str, Any]:
        """Get information about study agents."""
        agents = {
            "director": {
                "port": 10401,
                "role": "Orchestration",
                "model": "glm-5",
                "status": "running",
                "description": "Coordinates study tasks and workflows"
            },
            "executor": {
                "port": 10402,
                "role": "Execution",
                "model": "glm-4.7",
                "status": "running",
                "description": "Executes specific study tasks"
            },
            "guardian": {
                "port": 10403,
                "role": "Validation",
                "model": "phi3-local",
                "status": "running",
                "description": "Validates quality and security"
            },
            "council": {
                "port": 10404,
                "role": "Consensus",
                "models": ["glm-5", "glm-4.7", "phi3-local"],
                "status": "running",
                "description": "Multi-model consensus system"
            },
            "study_domain": {
                "port": 10500,
                "role": "Coordination",
                "status": "running",
                "description": "Coordinates all study blocks"
            }
        }
        return agents
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        services = self.get_services_status()
        study_progress = self.get_study_progress()
        
        total_services = len(services)
        running_services = len([s for s in services.values() if "Up" in s["status"]])
        
        metrics = {
            "total_services": total_services,
            "running_services": running_services,
            "uptime_percentage": round((running_services / total_services) * 100, 1),
            "study_agents": 5,
            "topics": study_progress.get("topics_configured", 34),
            "techniques": 156,
            "blocks_initialized": study_progress.get("blocks_initialized", 5),
            "last_updated": datetime.now().isoformat()
        }
        
        return metrics
    
    def send_command_to_agent(self, agent_name: str, command: dict) -> Dict[str, Any]:
        """Send command to a specific agent (placeholder)."""
        # In production, this would use NATS messaging
        return {
            "success": True,
            "message": f"Command sent to {agent_name}",
            "command": command,
            "timestamp": datetime.now().isoformat()
        }


# Initialize API
api = MissionControlAPI()

@app.route('/')
def index():
    """Serve main dashboard."""
    try:
        with open('/app/config/index.html', 'r') as f:
            return f.read()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get overall system status."""
    return jsonify({
        "services": api.get_services_status(),
        "metrics": api.get_system_metrics(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/agents')
def get_agents():
    """Get agents information."""
    return jsonify({
        "agents": api.get_agents_info(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/study')
def get_study():
    """Get study domain progress."""
    return jsonify({
        "progress": api.get_study_progress(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/command/<agent_name>', methods=['POST'])
def send_command(agent_name):
    """Send command to an agent."""
    try:
        command = request.json
        result = api.send_command_to_agent(agent_name, command)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "5.0.0"
    })

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=80, debug=False)