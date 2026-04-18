"""
Federation — NATS Client

Connects to Jart-OS NATS JetStream for inter-service messaging.
Subject taxonomy: jart-os.<tier>.<domain>.<function>.<action>

See: documentation/COMMUNICATION-FLOWS.md
"""

import logging
from typing import Any

import nats
from nats.js import JetStreamContext


class NATSClient:
    """NATS JetStream client for Jart-OS federation."""

    def __init__(self, url: str = "nats://nats:4222"):
        self.url = url
        self.nc: nats.NATS | None = None
        self.js: JetStreamContext | None = None
        self.log = logging.getLogger("jart-os.federation.nats")

    async def connect(self):
        """Connect to NATS and get JetStream context."""
        self.nc = await nats.connect(self.url)
        self.js = self.nc.jetstream()
        self.log.info(f"Connected to NATS: {self.url}")

    async def disconnect(self):
        """Graceful disconnect."""
        if self.nc:
            await self.nc.close()
            self.log.info("Disconnected from NATS")

    async def publish(self, subject: str, payload: dict):
        """Publish message to NATS subject."""
        if not self.nc:
            raise RuntimeError("NATS not connected")
        import json
        await self.nc.publish(subject, json.dumps(payload).encode())
        self.log.debug(f"Published to {subject}")

    async def subscribe(self, subject: str, handler):
        """Subscribe to NATS subject with handler."""
        if not self.nc:
            raise RuntimeError("NATS not connected")
        await self.nc.subscribe(subject, cb=handler)
        self.log.info(f"Subscribed to {subject}")
