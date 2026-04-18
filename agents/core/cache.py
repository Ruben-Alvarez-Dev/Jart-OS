"""
Jart-OS CacheManager — 3-level caching (L1 in-memory, L2 Redis, L3 optional)
Spec: Fase 5 Punto 2 — Optimizacion de Rendimiento
"""

import os
import json
import time
import hashlib
import logging
from typing import Optional, Any

log = logging.getLogger("jart-os.core.cache")


class CacheManager:
    """
    3-level cache: L1 (in-memory) -> L2 (Redis) -> Source.

    L1: Python dict, TTL 5 min, per-process
    L2: Redis, TTL 15 min, shared across agents
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.l1_cache: dict = {}
        self.l1_ttl: int = int(os.getenv("CACHE_L1_TTL", "300"))   # 5 min
        self.l2_ttl: int = int(os.getenv("CACHE_L2_TTL", "900"))   # 15 min
        self.l2_prefix: str = "jart-os:cache:"
        self.hits = 0
        self.misses = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Lookup: L1 -> L2 -> None."""
        # L1
        entry = self.l1_cache.get(key)
        if entry is not None:
            value, ts = entry
            if time.time() - ts < self.l1_ttl:
                self.hits += 1
                return value
            del self.l1_cache[key]

        # L2
        if self.redis:
            raw = self.redis.get(f"{self.l2_prefix}{key}")
            if raw is not None:
                value = json.loads(raw)
                # promote to L1
                self.l1_cache[key] = (value, time.time())
                self.hits += 1
                return value

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int = None):
        """Write L1 + L2."""
        self.l1_cache[key] = (value, time.time())

        if self.redis:
            cache_ttl = ttl or self.l2_ttl
            self.redis.setex(
                f"{self.l2_prefix}{key}",
                cache_ttl,
                json.dumps(value, default=str),
            )

    def invalidate(self, key: str):
        """Remove from L1 + L2."""
        self.l1_cache.pop(key, None)
        if self.redis:
            self.redis.delete(f"{self.l2_prefix}{key}")

    def invalidate_pattern(self, pattern: str):
        """Remove all keys matching pattern from L2."""
        # Clear matching L1 entries
        keys_to_remove = [k for k in self.l1_cache if pattern in k]
        for k in keys_to_remove:
            del self.l1_cache[k]

        # Clear matching L2 entries
        if self.redis:
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(
                    cursor, match=f"{self.l2_prefix}{pattern}", count=100
                )
                if keys:
                    self.redis.delete(*keys)
                if cursor == 0:
                    break

    def clear(self):
        """Clear all caches."""
        self.l1_cache.clear()
        if self.redis:
            self.invalidate_pattern("*")

    @staticmethod
    def make_key(*parts) -> str:
        """Deterministic cache key from parts."""
        raw = "|".join(str(p) for p in parts)
        return hashlib.sha256(raw.encode()).hexdigest()

    def stats(self) -> dict:
        """Return cache hit/miss stats."""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0,
            "l1_size": len(self.l1_cache),
        }
