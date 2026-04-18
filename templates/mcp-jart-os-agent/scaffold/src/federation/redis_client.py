"""
Federation — Redis Client

State management via Redis.
Key patterns: jart-os:{function}:*

See: documentation/API-REFERENCE.md
"""

import json
import logging
from typing import Any

import redis.asyncio as aioredis


class RedisClient:
    """Async Redis client for Jart-OS federation state."""

    def __init__(self, url: str = "redis://redis:6379"):
        self.url = url
        self.redis: aioredis.Redis | None = None
        self.log = logging.getLogger("jart-os.federation.redis")
        self.prefix = "jart-os:{function}:"

    async def connect(self):
        """Connect to Redis."""
        self.redis = aioredis.from_url(self.url, decode_responses=True)
        self.log.info(f"Connected to Redis: {self.url}")

    async def disconnect(self):
        """Graceful disconnect."""
        if self.redis:
            await self.redis.close()
            self.log.info("Disconnected from Redis")

    async def get(self, key: str) -> dict | None:
        """Get state by key."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        data = await self.redis.get(f"{self.prefix}{key}")
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, ttl: int | None = None):
        """Set state with optional TTL."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        full_key = f"{self.prefix}{key}"
        await self.redis.set(full_key, json.dumps(value), ex=ttl)

    async def delete(self, key: str):
        """Delete state by key."""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        await self.redis.delete(f"{self.prefix}{key}")
