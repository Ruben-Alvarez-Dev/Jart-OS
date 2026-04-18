"""
Jart-OS BatchManager — Collect items and flush in bulk
Spec: Fase 5 Punto 2 — Optimizacion de Rendimiento
"""

import time
import json
import logging
import threading
from typing import List, Callable, Any

log = logging.getLogger("jart-os.core.batch")


class BatchManager:
    """
    Collects items and flushes them in bulk when either:
    - batch_size is reached, OR
    - timeout elapses (whichever comes first).

    Usage:
        def my_handler(items):
            for item in items:
                redis.set(item['key'], item['value'])

        bm = BatchManager(handler=my_handler, batch_size=50, timeout=10)
        bm.add({"key": "k1", "value": "v1"})
        bm.add({"key": "k2", "value": "v2"})
        # ... after 50 items OR 10 seconds, handler fires automatically
    """

    def __init__(
        self,
        handler: Callable[[List[Any]], None],
        batch_size: int = 50,
        timeout: float = 10.0,
        name: str = "default",
    ):
        self.handler = handler
        self.batch_size = batch_size
        self.timeout = timeout
        self.name = name

        self._buffer: List[Any] = []
        self._lock = threading.Lock()
        self._timer: threading.Timer = None
        self._flushed = 0
        self._errors = 0

        log.info(f"BatchManager '{name}' initialized (size={batch_size}, timeout={timeout}s)")

    def add(self, item: Any):
        """Add item to buffer. Flush if batch_size reached."""
        with self._lock:
            self._buffer.append(item)
            count = len(self._buffer)

        if count >= self.batch_size:
            self.flush()
        else:
            self._reset_timer()

    def flush(self):
        """Flush buffer and call handler."""
        with self._lock:
            batch = self._buffer[:]
            self._buffer.clear()

        if not batch:
            return

        self._cancel_timer()

        try:
            self.handler(batch)
            self._flushed += len(batch)
            log.debug(f"Batch '{self.name}' flushed {len(batch)} items")
        except Exception as e:
            self._errors += 1
            log.error(f"Batch '{self.name}' error: {e}")

    def stats(self) -> dict:
        """Return batch stats."""
        return {
            "name": self.name,
            "buffer_size": len(self._buffer),
            "flushed_total": self._flushed,
            "errors_total": self._errors,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _reset_timer(self):
        self._cancel_timer()
        self._timer = threading.Timer(self.timeout, self.flush)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
