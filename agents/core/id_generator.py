"""
Jart-OS ID Generator — Hybrid ULID + Semantic IDs
Spec: Fase 5 Punto 1 — Escalado Horizontal
       Fase 5 Punto 3 — Implementación de IDs híbridos

Format: {prefix}-{ulid}
Ejemplos:
  - task-01H3Z4J2X8Z0Y9Z2X9Z2X9Z2X9
  - agent-01H3Z4J2X8Z0Y9Z2X9Z2X9Z2X9
  - session-01H3Z4J2X8Z0Y9Z2X9Z2X9Z2X9
"""

import time
import re
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

try:
    from ulid import ULID
    HAS_ULID = True
except ImportError:
    HAS_ULID = False
    import uuid
    print("WARNING: ulid-py not installed. Falling back to UUID. pip install ulid-py")


class IDPrefix(Enum):
    """Prefixes for different ID types."""
    TASK = "task"
    AGENT = "agent"
    SESSION = "session"
    CHUNK = "chunk"
    EVENT = "event"
    AUDIT = "audit"
    METRIC = "metric"
    LOG = "log"


@dataclass
class IDInfo:
    """Parsed information from a hybrid ID."""
    prefix: str
    ulid: str
    full_id: str
    timestamp: float
    is_valid: bool


class IDGenerator:
    """Generates and validates hybrid ULID + semantic IDs."""
    
    def __init__(self):
        self._validate_ulid_available()
    
    def generate(self, prefix: IDPrefix) -> str:
        """
        Generate a hybrid ID: {prefix}-{ulid}
        
        Args:
            prefix: IDPrefix enum value (e.g., IDPrefix.TASK)
        
        Returns:
            Hybrid ID string (e.g., "task-01H3Z4J2X8Z0Y9Z2X9Z2X9Z2X9")
        
        Raises:
            ValueError: If prefix is invalid
        """
        if not isinstance(prefix, IDPrefix):
            raise ValueError(f"prefix must be IDPrefix enum, got {type(prefix)}")
        
        prefix_str = prefix.value
        
        if HAS_ULID:
            ulid = str(ULID())
        else:
            # Fallback to UUID v4
            ulid = str(uuid.uuid4())
        
        return f"{prefix_str}-{ulid}"
    
    def generate_task(self) -> str:
        """Generate a task ID."""
        return self.generate(IDPrefix.TASK)
    
    def generate_agent(self) -> str:
        """Generate an agent ID."""
        return self.generate(IDPrefix.AGENT)
    
    def generate_session(self) -> str:
        """Generate a session ID."""
        return self.generate(IDPrefix.SESSION)
    
    def generate_chunk(self) -> str:
        """Generate a chunk ID."""
        return self.generate(IDPrefix.CHUNK)
    
    def generate_event(self) -> str:
        """Generate an event ID."""
        return self.generate(IDPrefix.EVENT)
    
    def generate_audit(self) -> str:
        """Generate an audit ID."""
        return self.generate(IDPrefix.AUDIT)
    
    def generate_metric(self) -> str:
        """Generate a metric ID."""
        return self.generate(IDPrefix.METRIC)
    
    def generate_log(self) -> str:
        """Generate a log ID."""
        return self.generate(IDPrefix.LOG)
    
    def parse(self, hybrid_id: str) -> IDInfo:
        """
        Parse a hybrid ID into its components.
        
        Args:
            hybrid_id: Hybrid ID string (e.g., "task-01H3Z4J2X8Z0Y9Z2X9Z2X9Z2X9")
        
        Returns:
            IDInfo object with parsed information
        """
        # Validate format
        pattern = r"^([a-z]+)-([A-Z0-9]{26})$"
        match = re.match(pattern, hybrid_id)
        
        if not match:
            return IDInfo(
                prefix="",
                ulid="",
                full_id=hybrid_id,
                timestamp=0.0,
                is_valid=False,
            )
        
        prefix = match.group(1)
        ulid = match.group(2)
        
        # Extract timestamp from ULID
        if HAS_ULID:
            try:
                ulid_obj = ULID.from_str(ulid)
                timestamp = ulid_obj.datetime.timestamp()
            except Exception:
                timestamp = 0.0
        else:
            # UUID doesn't have timestamp, use current time
            timestamp = time.time()
        
        return IDInfo(
            prefix=prefix,
            ulid=ulid,
            full_id=hybrid_id,
            timestamp=timestamp,
            is_valid=True,
        )
    
    def is_valid(self, hybrid_id: str) -> bool:
        """
        Validate a hybrid ID.
        
        Args:
            hybrid_id: Hybrid ID string to validate
        
        Returns:
            True if valid, False otherwise
        """
        info = self.parse(hybrid_id)
        return info.is_valid
    
    def get_timestamp(self, hybrid_id: str) -> float:
        """
        Extract timestamp from a hybrid ID.
        
        Args:
            hybrid_id: Hybrid ID string
        
        Returns:
            Unix timestamp (seconds since epoch)
        """
        info = self.parse(hybrid_id)
        return info.timestamp
    
    def get_prefix(self, hybrid_id: str) -> str:
        """
        Extract prefix from a hybrid ID.
        
        Args:
            hybrid_id: Hybrid ID string
        
        Returns:
            Prefix string (e.g., "task", "agent")
        """
        info = self.parse(hybrid_id)
        return info.prefix
    
    def filter_by_prefix(self, ids: List[str], prefix: IDPrefix) -> List[str]:
        """
        Filter a list of hybrid IDs by prefix.
        
        Args:
            ids: List of hybrid IDs
            prefix: IDPrefix to filter by
        
        Returns:
            Filtered list of IDs
        """
        prefix_str = prefix.value
        return [id for id in ids if id.startswith(f"{prefix_str}-")]
    
    def sort_by_timestamp(self, ids: List[str], reverse: bool = False) -> List[str]:
        """
        Sort hybrid IDs by timestamp (chronological order).
        
        Args:
            ids: List of hybrid IDs
            reverse: If True, sort descending (newest first)
        
        Returns:
            Sorted list of IDs
        """
        def get_timestamp(id_str):
            return self.get_timestamp(id_str)
        
        return sorted(ids, key=get_timestamp, reverse=reverse)
    
    def _validate_ulid_available(self):
        """Check if ulid-py is available and warn if not."""
        if not HAS_ULID:
            print("=" * 70)
            print("WARNING: ulid-py not installed")
            print("Falling back to UUID (not sortable by time)")
            print("Install with: pip install ulid-py")
            print("=" * 70)


# Singleton instance
_id_generator = None

def get_id_generator() -> IDGenerator:
    """Get singleton IDGenerator instance."""
    global _id_generator
    if _id_generator is None:
        _id_generator = IDGenerator()
    return _id_generator


# Convenience functions
def generate_id(prefix: IDPrefix) -> str:
    """Generate a hybrid ID (convenience function)."""
    return get_id_generator().generate(prefix)


def generate_task_id() -> str:
    """Generate a task ID (convenience function)."""
    return get_id_generator().generate_task()


def generate_agent_id() -> str:
    """Generate an agent ID (convenience function)."""
    return get_id_generator().generate_agent()


def generate_session_id() -> str:
    """Generate a session ID (convenience function)."""
    return get_id_generator().generate_session()


def generate_chunk_id() -> str:
    """Generate a chunk ID (convenience function)."""
    return get_id_generator().generate_chunk()


def generate_event_id() -> str:
    """Generate an event ID (convenience function)."""
    return get_id_generator().generate_event()


def generate_audit_id() -> str:
    """Generate an audit ID (convenience function)."""
    return get_id_generator().generate_audit()


def parse_id(hybrid_id: str) -> IDInfo:
    """Parse a hybrid ID (convenience function)."""
    return get_id_generator().parse(hybrid_id)


def is_valid_id(hybrid_id: str) -> bool:
    """Validate a hybrid ID (convenience function)."""
    return get_id_generator().is_valid(hybrid_id)


def get_id_timestamp(hybrid_id: str) -> float:
    """Extract timestamp from a hybrid ID (convenience function)."""
    return get_id_generator().get_timestamp(hybrid_id)


# Example usage
if __name__ == "__main__":
    # Create generator
    gen = get_id_generator()
    
    # Generate IDs
    task_id = gen.generate_task()
    agent_id = gen.generate_agent()
    session_id = gen.generate_session()
    chunk_id = gen.generate_chunk()
    
    print(f"Task ID: {task_id}")
    print(f"Agent ID: {agent_id}")
    print(f"Session ID: {session_id}")
    print(f"Chunk ID: {chunk_id}")
    
    # Parse ID
    info = gen.parse(task_id)
    print(f"\nParsed ID: {info.full_id}")
    print(f"  Prefix: {info.prefix}")
    print(f"  ULID: {info.ulid}")
    print(f"  Timestamp: {info.timestamp}")
    print(f"  Valid: {info.is_valid}")
    
    # Sort IDs by timestamp
    ids = [task_id, agent_id, session_id, chunk_id]
    sorted_ids = gen.sort_by_timestamp(ids)
    print(f"\nSorted IDs: {sorted_ids}")
    
    # Filter by prefix
    task_ids = gen.filter_by_prefix(ids, IDPrefix.TASK)
    print(f"Task IDs: {task_ids}")
