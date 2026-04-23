from typing import Dict

import hashlib
import time
import logging

log = logging.getLogger("alfred.intelligence.dedup")


class Deduplicator:
    """Prevents processing the same message or link twice."""

    def __init__(self, ttl_seconds: int = 86400):
        self._seen: Dict[str, float] = {}
        self.ttl = ttl_seconds

    def is_duplicate(self, content: str) -> bool:
        """Check if we've seen this content recently."""
        self._prune()
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        if content_hash in self._seen:
            return True
        self._seen[content_hash] = time.time()
        return False

    def _prune(self):
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, v in self._seen.items() if now - v > self.ttl]
        for k in expired:
            del self._seen[k]
