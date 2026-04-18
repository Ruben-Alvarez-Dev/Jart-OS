"""
Jart-OS Blockchain Lite — Append-only audit trail
Spec: Fase 5 Punto 4 — Blockchain ligera para audit trail
"""

import json
import hashlib
import time
import logging
from typing import Optional
from datetime import datetime, timezone

log = logging.getLogger("jart-os.core.blockchain")


class Block:
    """A single block in the chain."""

    def __init__(
        self,
        index: int,
        prev_hash: str,
        event_id: str,
        agent: str,
        action: str,
        payload: dict,
        timestamp: float = None,
        nonce: int = 0,
        block_hash: str = None,
    ):
        self.index = index
        self.prev_hash = prev_hash
        self.event_id = event_id
        self.agent = agent
        self.action = action
        self.payload = payload
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.block_hash = block_hash  # computed after mining

    def compute_hash(self) -> str:
        """SHA-256 of block contents."""
        data = json.dumps({
            "index": self.index,
            "prev_hash": self.prev_hash,
            "event_id": self.event_id,
            "agent": self.agent,
            "action": self.action,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()

    def mine(self, difficulty: int = 3) -> int:
        """Proof of Work: find nonce so hash starts with N zeros."""
        target = "0" * difficulty
        self.nonce = 0
        while not self.compute_hash().startswith(target):
            self.nonce += 1
        self.block_hash = self.compute_hash()
        return self.nonce

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "event_id": self.event_id,
            "agent": self.agent,
            "action": self.action,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "block_hash": self.block_hash,
        }


class BlockchainLite:
    """
    Lightweight append-only blockchain stored in Redis.

    Usage:
        bc = BlockchainLite(redis_client)
        block = bc.add_block("event-xxx", "director", "task_created", {"obj": "study T5"})
        assert bc.verify_chain()
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, redis_client=None, difficulty: int = 3):
        self.redis = redis_client
        self.difficulty = difficulty
        self.chain_key = "jart-os:blockchain:chain"
        self.latest_key = "jart-os:blockchain:latest"

    def add_block(self, event_id: str, agent: str, action: str, payload: dict) -> Block:
        """Create, mine, and store a new block."""
        # Get previous
        prev_index, prev_hash = self._get_last()
        index = prev_index + 1

        block = Block(
            index=index,
            prev_hash=prev_hash,
            event_id=event_id,
            agent=agent,
            action=action,
            payload=payload,
        )

        # Mine
        attempts = block.mine(self.difficulty)
        log.info(f"Block #{index} mined (nonce={attempts}, hash={block.block_hash[:16]}...)")

        # Store
        if self.redis:
            self.redis.hset(self.chain_key, str(index), json.dumps(block.to_dict(), default=str))
            self.redis.set(self.latest_key, str(index))

        return block

    def get_block(self, index: int) -> Optional[Block]:
        """Get block by index."""
        if not self.redis:
            return None
        raw = self.redis.hget(self.chain_key, str(index))
        if not raw:
            return None
        d = json.loads(raw)
        return Block(**d)

    def get_latest(self) -> Optional[Block]:
        """Get latest block."""
        if not self.redis:
            return None
        raw = self.redis.get(self.latest_key)
        if not raw:
            return None
        return self.get_block(int(raw))

    def chain_length(self) -> int:
        """Total blocks."""
        latest = self.get_latest()
        return (latest.index + 1) if latest else 0

    def verify_chain(self) -> bool:
        """Verify integrity of entire chain."""
        latest = self.get_latest()
        if not latest:
            return True  # empty chain is valid

        current = latest
        while current.index > 0:
            # Check hash
            if current.block_hash != current.compute_hash():
                log.error(f"Block #{current.index} hash mismatch!")
                return False
            # Check link
            prev = self.get_block(current.index - 1)
            if not prev:
                log.error(f"Block #{current.index - 1} missing!")
                return False
            if current.prev_hash != prev.block_hash:
                log.error(f"Block #{current.index} prev_hash mismatch!")
                return False
            current = prev

        # Genesis check
        if current.prev_hash != self.GENESIS_HASH:
            log.error("Genesis block prev_hash invalid!")
            return False

        return True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_last(self):
        latest = self.get_latest()
        if latest:
            return latest.index, latest.block_hash
        return -1, self.GENESIS_HASH
