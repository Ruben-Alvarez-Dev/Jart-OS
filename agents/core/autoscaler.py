"""
Jart-OS Autoscaler — Auto-scale services based on metrics
Spec: Fase 5 Punto 6 — Gestion de Recursos
"""

import json
import time
import logging
import subprocess
from typing import Dict, Optional

log = logging.getLogger("jart-os.core.autoscaler")


class Autoscaler:
    """
    Monitor service metrics and scale replicas up/down.

    Thresholds:
    - Scale UP:   CPU > 80%, Memory > 80%, Queue > 100
    - Scale DOWN:  CPU < 30%, Memory < 30%, Queue < 10

    Limits:
    - Max replicas: 5
    - Min replicas: 1
    """

    SCALE_UP_THRESHOLD = 0.8
    SCALE_DOWN_THRESHOLD = 0.3
    MAX_REPLICAS = 5
    MIN_REPLICAS = 1

    # Services that support scaling (stateless workers)
    SCALABLE_SERVICES = {
        "executor-study": {"min": 1, "max": 5},
        "pipe-pdf": {"min": 1, "max": 3},
        "pipe-photos": {"min": 1, "max": 3},
        "pipe-video": {"min": 1, "max": 2},
        "pipe-rag": {"min": 1, "max": 3},
    }

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.metrics_key = "jart-os:metrics"
        self.scale_events_key = "jart-os:autoscaler:events"

    def check_and_scale(self):
        """Check metrics for all scalable services and scale if needed."""
        for service in self.SCALABLE_SERVICES:
            metrics = self._get_metrics(service)

            if not metrics:
                continue

            config = self.SCALABLE_SERVICES[service]
            current = self._get_replicas(service)

            # Scale UP?
            if (
                metrics.get("cpu", 0) > self.SCALE_UP_THRESHOLD
                or metrics.get("memory", 0) > self.SCALE_UP_THRESHOLD
                or metrics.get("queue_size", 0) > 100
            ):
                if current < config["max"]:
                    self._scale(service, current + 1, "up", metrics)
                    return

            # Scale DOWN?
            if (
                metrics.get("cpu", 1) < self.SCALE_DOWN_THRESHOLD
                and metrics.get("memory", 1) < self.SCALE_DOWN_THRESHOLD
                and metrics.get("queue_size", 999) < 10
            ):
                if current > config["min"]:
                    self._scale(service, current - 1, "down", metrics)

    def _scale(self, service: str, target: int, direction: str, metrics: dict):
        """Scale a service to target replicas."""
        log.info(f"Scaling {service} {direction}: {target} replicas (cpu={metrics.get('cpu', '?')})")

        # Log event
        event = {
            "service": service,
            "direction": direction,
            "target_replicas": target,
            "metrics": metrics,
            "timestamp": time.time(),
        }
        if self.redis:
            self.redis.lpush(self.scale_events_key, json.dumps(event, default=str))

        # Docker compose scale
        try:
            cmd = f"cd $JART_OS_HOME && docker compose up -d --scale {service}={target}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                log.info(f"Scaled {service} to {target} replicas")
            else:
                log.error(f"Scale failed: {result.stderr[:200]}")
        except Exception as e:
            log.error(f"Scale command error: {e}")

    def _get_metrics(self, service: str) -> Optional[dict]:
        """Get metrics from Redis."""
        if not self.redis:
            return None
        raw = self.redis.get(f"{self.metrics_key}:{service}")
        if raw:
            return json.loads(raw)
        return None

    def _get_replicas(self, service: str) -> int:
        """Get current replica count via docker."""
        try:
            result = subprocess.run(
                f"docker ps --filter name=jart-os-{service} --format '{{{{.Names}}}}'",
                shell=True, capture_output=True, text=True, timeout=10,
            )
            if result.stdout:
                return len(result.stdout.strip().split("\n"))
        except Exception:
            pass
        return 1

    def get_status(self) -> dict:
        """Get current scaling status."""
        status = {}
        for service in self.SCALABLE_SERVICES:
            status[service] = {
                "current_replicas": self._get_replicas(service),
                "config": self.SCALABLE_SERVICES[service],
                "metrics": self._get_metrics(service),
            }
        return status
