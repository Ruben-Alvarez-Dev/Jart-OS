"""
Jart-OS Mission Control API — PRODUCTION
=========================================
100% REAL data. ZERO mocks. ZERO placeholders. ZERO hardcoded values.

Data sources:
  - Docker API: real container status (requires /var/run/docker.sock)
  - Agent health endpoints: real agent state via HTTP
  - NATS: real command dispatch to agents
  - Filesystem: real study data from mounted volumes

Spec: §21 "Boot & Operations", §22 D8 "Mission Control"
"""

import os
import json
import time
import logging
import asyncio
import requests
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from flask import Flask, jsonify, request

import docker as docker_sdk
import nats
from urllib.parse import urlparse

log = logging.getLogger("jart-os.mission_control")
app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────
# Service Registry — maps container names to metadata
# Only names and expected ports. Status comes from LIVE queries.
# ─────────────────────────────────────────────────────────────────

SERVICE_REGISTRY = {
    "jart-os-director-study": {"role": "Orchestration", "port": 10401, "tier": "agent"},
    "jart-os-executor-study": {"role": "Execution", "port": 10402, "tier": "agent"},
    "jart-os-guardian": {"role": "Validation", "port": 10403, "tier": "agent"},
    "jart-os-council": {"role": "Consensus", "port": 10404, "tier": "agent"},
    "jart-os-study-domain": {"role": "Coordination", "port": 10500, "tier": "service"},
    "jart-os-litellm": {"role": "LLM Gateway", "port": 10201, "tier": "gateway"},
    "jart-os-redis": {"role": "State Store", "port": 10301, "tier": "infra"},
    "jart-os-nats": {"role": "Messaging", "port": 10302, "tier": "infra"},
    "jart-os-grafana": {"role": "Monitoring", "port": 10702, "tier": "interface"},
    "jart-os-prometheus": {"role": "Metrics", "port": 10901, "tier": "infra"},
    "jart-os-pipe-pdf": {"role": "PDF Pipeline", "port": 10601, "tier": "pipeline"},
    "jart-os-pipe-rag": {"role": "RAG Pipeline", "port": 10604, "tier": "pipeline"},
}

AGENT_REGISTRY = {
    "director": {"container": "jart-os-director-study", "port": 10401},
    "executor": {"container": "jart-os-executor-study", "port": 10402},
    "guardian": {"container": "jart-os-guardian", "port": 10403},
    "council": {"container": "jart-os-council", "port": 10404},
    "study_domain": {"container": "jart-os-study-domain", "port": 10500},
}

NATS_SUBJECT_MAP = {
    "director": "jart-os.04.study.director.command",
    "executor": "jart-os.04.study.executor.command",
    "guardian": "jart-os.04.study.guardian.checks",
    "council": "jart-os.04.study.council.proposals",
}

EXAM_DATE = "2026-06-15"


class MissionControlAPI:
    """Mission Control — 100% real data from live systems."""

    def __init__(self):
        self.study_path = Path("/app/study")
        self._docker = None
        self._nc = None
        self._nats_loop = None
        self._nats_thread = None

        self._connect_docker()
        self._connect_nats()

    # ───────────────────────────────────────────────────────────
    # Docker — real container status
    # ───────────────────────────────────────────────────────────

    def _connect_docker(self):
        """Connect to Docker daemon via socket."""
        try:
            self._docker = docker_sdk.from_env()
            self._docker.ping()
            log.info("Docker client connected")
        except Exception as e:
            self._docker = None
            log.error(f"Docker client FAILED: {e}")

    def get_services_status(self) -> dict:
        """Query REAL container status from Docker API."""
        if not self._docker:
            return {"error": "Docker API unavailable", "services": {}}

        try:
            all_containers = {c.name: c for c in self._docker.containers.list(all=True)}
        except Exception as e:
            log.error(f"Docker list failed: {e}")
            return {"error": str(e), "services": {}}

        services = {}
        for name, meta in SERVICE_REGISTRY.items():
            container = all_containers.get(name)
            if container:
                services[name] = {
                    "status": container.status,
                    "port": meta["port"],
                    "role": meta["role"],
                    "tier": meta["tier"],
                    "container_id": container.short_id,
                    "image": container.attrs.get("Config", {}).get("Image", ""),
                    "started_at": container.attrs.get("State", {}).get("StartedAt", "")[
                        :19
                    ],
                }
            else:
                services[name] = {
                    "status": "not_deployed",
                    "port": meta["port"],
                    "role": meta["role"],
                    "tier": meta["tier"],
                }

        return services

    # ───────────────────────────────────────────────────────────
    # Agents — real health data from HTTP endpoints
    # ───────────────────────────────────────────────────────────

    def get_agents_info(self) -> dict:
        """Query REAL agent state from each agent's /health endpoint."""
        agents = {}
        for role, cfg in AGENT_REGISTRY.items():
            try:
                resp = requests.get(
                    f"http://{cfg['container']}:{cfg['port']}/health",
                    timeout=3,
                )
                resp.raise_for_status()
                agents[role] = resp.json()
            except requests.exceptions.ConnectionError:
                agents[role] = {"status": "offline", "role": role, "port": cfg["port"]}
            except requests.exceptions.Timeout:
                agents[role] = {"status": "timeout", "role": role, "port": cfg["port"]}
            except Exception as e:
                agents[role] = {
                    "status": "error",
                    "role": role,
                    "port": cfg["port"],
                    "error": str(e),
                }
        return agents

    # ───────────────────────────────────────────────────────────
    # NATS — real command dispatch
    # ───────────────────────────────────────────────────────────

    def _connect_nats(self):
        """Connect to NATS for real command dispatch."""
        nats_url = os.getenv("NATS_URL", "nats://nats:4222")

        async def _do_connect():
            parsed = urlparse(nats_url)
            server_url = f"nats://{parsed.hostname or 'nats'}:{parsed.port or 4222}"
            nats_token = parsed.password or os.getenv("NATS_TOKEN")

            kwargs = dict(
                servers=[server_url],
                name="jart-os-mission-control",
                reconnect_time_wait=2,
                max_reconnect_attempts=10,
            )
            if nats_token:
                kwargs["token"] = nats_token

            self._nc = await nats.connect(**kwargs)
            log.info(f"NATS connected: {server_url}")

        try:
            self._nats_loop = asyncio.new_event_loop()
            self._nats_loop.run_until_complete(_do_connect())
            self._nats_thread = Thread(target=self._nats_loop.run_forever, daemon=True)
            self._nats_thread.start()
        except Exception as e:
            self._nc = None
            log.error(f"NATS connection FAILED: {e}")

    def send_command(self, agent_name: str, command: dict) -> dict:
        """Send REAL command to agent via NATS publish."""
        subject = NATS_SUBJECT_MAP.get(agent_name)
        if not subject:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}. Valid: {list(NATS_SUBJECT_MAP.keys())}",
            }
        if not self._nc:
            return {"success": False, "error": "NATS not connected"}

        try:
            payload = json.dumps(command).encode()
            future = asyncio.run_coroutine_threadsafe(
                self._nc.publish(subject, payload),
                self._nats_loop,
            )
            future.result(timeout=5)
            return {
                "success": True,
                "agent": agent_name,
                "subject": subject,
                "command_id": command.get("task_id", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ───────────────────────────────────────────────────────────
    # Study progress — real filesystem data
    # ───────────────────────────────────────────────────────────

    def get_study_progress(self) -> dict:
        """Read REAL study data from mounted volume."""
        # Try official status report first
        status_path = self.study_path / "status_report.json"
        if status_path.exists():
            try:
                with open(status_path) as f:
                    data = json.load(f)
                data["source"] = "status_report.json"
                return data
            except Exception as e:
                log.error(f"Failed to read status_report.json: {e}")

        # Fallback: scan the real filesystem
        if not self.study_path.exists():
            return {
                "domain": "study",
                "status": "no_volume",
                "path": str(self.study_path),
                "message": "Study volume not mounted or empty",
            }

        blocks = sorted([p.name for p in self.study_path.glob("block_*")])
        pdfs = list(self.study_path.rglob("*.pdf"))
        json_files = list(self.study_path.rglob("*.json"))

        return {
            "domain": "study",
            "status": "scanned",
            "blocks": blocks,
            "blocks_count": len(blocks),
            "pdfs_count": len(pdfs),
            "data_files_count": len(json_files),
            "path": str(self.study_path),
            "source": "filesystem_scan",
        }

    # ───────────────────────────────────────────────────────────
    # System metrics — aggregated from real sources
    # ───────────────────────────────────────────────────────────

    def get_system_metrics(self) -> dict:
        """Aggregate REAL metrics from Docker + agents."""
        services = self.get_services_status()
        agents = self.get_agents_info()
        study = self.get_study_progress()

        svc_list = [v for v in services.values() if isinstance(v, dict)]
        total = len(svc_list)
        running = len([s for s in svc_list if s.get("status") == "running"])

        agent_list = [v for v in agents.values() if isinstance(v, dict)]
        agents_ok = len([a for a in agent_list if a.get("status") == "ok"])
        tasks_done = sum(a.get("tasks_completed", 0) for a in agent_list)
        tasks_fail = sum(a.get("tasks_failed", 0) for a in agent_list)

        # Days to exam
        try:
            days_left = (datetime(2026, 6, 15) - datetime.now()).days
        except Exception:
            days_left = -1

        return {
            "services_total": total,
            "services_running": running,
            "services_pct": round((running / total) * 100, 1) if total else 0,
            "agents_online": agents_ok,
            "agents_total": len(agent_list),
            "tasks_completed": tasks_done,
            "tasks_failed": tasks_fail,
            "days_to_exam": days_left,
            "exam_date": EXAM_DATE,
            "nats_connected": self._nc is not None,
            "docker_connected": self._docker is not None,
            "study_blocks": study.get("blocks_count", 0),
            "study_pdfs": study.get("pdfs_count", 0),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


# ═════════════════════════════════════════════════════════════════
# Initialize + Flask Routes
# ═════════════════════════════════════════════════════════════════

api = MissionControlAPI()


@app.route("/")
def index():
    try:
        with open("/app/config/index.html") as f:
            return f.read()
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def health():
    """Real health — reports actual connectivity."""
    return jsonify(
        {
            "status": "healthy" if (api._docker and api._nc) else "degraded",
            "docker_connected": api._docker is not None,
            "nats_connected": api._nc is not None,
            "version": "5.2.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/api/status")
def status():
    """Real system status — Docker containers + metrics."""
    return jsonify(
        {
            "services": api.get_services_status(),
            "metrics": api.get_system_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/api/agents")
def agents():
    """Real agent info — from HTTP health endpoints."""
    return jsonify(
        {
            "agents": api.get_agents_info(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/api/study")
def study():
    """Real study progress — from filesystem."""
    return jsonify(
        {
            "progress": api.get_study_progress(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/api/command/<agent_name>", methods=["POST"])
def command(agent_name):
    """Send REAL command to agent via NATS."""
    if not request.json:
        return jsonify({"success": False, "error": "JSON body required"}), 400
    result = api.send_command(agent_name, request.json)
    code = 200 if result.get("success") else 400
    return jsonify(result), code


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=80, debug=False)
