"""
Jart-OS AlertManager — Alertas y notificaciones del sistema
Spec: Fase 5 Punto 3 — Monitoreo Avanzado
"""

import os
import json
import time
import logging
import requests
from typing import Optional
from datetime import datetime, timezone

log = logging.getLogger("jart-os.core.alerts")


class AlertManager:
    """
    Gestiona alertas del sistema en 4 niveles de severidad:
    CRITICAL -> HIGH -> MEDIUM -> LOW

    Actions:
    - CRITICAL/HIGH: Discord webhook + Redis log
    - MEDIUM/LOW: Redis log only
    """

    SEVERITY_COLORS = {
        "CRITICAL": 0xFF0000,  # Red
        "HIGH": 0xFFA500,      # Orange
        "MEDIUM": 0xFFFF00,    # Yellow
        "LOW": 0x00FF00,       # Green
    }

    SEVERITY_EMOJI = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢",
    }

    def __init__(self, redis_client=None, discord_webhook: str = None):
        self.redis = redis_client
        self.discord_webhook = discord_webhook or os.getenv("DISCORD_WEBHOOK_URL", "")
        self.alerts_key = "jart-os:alerts"
        self.alert_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    def send(
        self,
        severity: str,
        service: str,
        message: str,
        details: dict = None,
    ):
        """Send alert to Redis + Discord (if CRITICAL/HIGH)."""
        alert = {
            "severity": severity,
            "service": service,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Count
        self.alert_counts[severity] = self.alert_counts.get(severity, 0) + 1

        # Store in Redis (keep last 1000)
        if self.redis:
            try:
                self.redis.lpush(self.alerts_key, json.dumps(alert, default=str))
                self.redis.ltrim(self.alerts_key, 0, 999)
            except Exception as e:
                log.error(f"Failed to store alert in Redis: {e}")

        # Log
        emoji = self.SEVERITY_EMOJI.get(severity, "⚪")
        log_method = {
            "CRITICAL": log.critical,
            "HIGH": log.error,
            "MEDIUM": log.warning,
            "LOW": log.info,
        }.get(severity, log.info)
        log_method(f"{emoji} [{severity}] {service}: {message}")

        # Discord for CRITICAL/HIGH
        if severity in ("CRITICAL", "HIGH") and self.discord_webhook:
            self._send_discord(alert)

    def get_recent(self, count: int = 50) -> list:
        """Get recent alerts from Redis."""
        if not self.redis:
            return []
        raw_list = self.redis.lrange(self.alerts_key, 0, count - 1)
        return [json.loads(a) for a in raw_list]

    def get_counts(self) -> dict:
        """Return alert counts since startup."""
        return dict(self.alert_counts)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _send_discord(self, alert: dict):
        """Send alert to Discord via webhook."""
        color = self.SEVERITY_COLORS.get(alert["severity"], 0x888888)
        emoji = self.SEVERITY_EMOJI.get(alert["severity"], "")

        payload = {
            "embeds": [{
                "title": f"{emoji} {alert['severity']}: {alert['service']}",
                "description": alert["message"],
                "color": color,
                "timestamp": alert["timestamp"],
                "fields": [
                    {"name": "Severity", "value": alert["severity"], "inline": True},
                    {"name": "Service", "value": alert["service"], "inline": True},
                ],
            }]
        }

        try:
            resp = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10,
            )
            if resp.status_code not in (200, 204):
                log.warning(f"Discord webhook returned {resp.status_code}")
        except Exception as e:
            log.error(f"Discord webhook failed: {e}")
