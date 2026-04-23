"""Message classifier — uses Haiku for dirt-cheap triage.

Maintains a session-local hash cache so the same message
isn't classified twice (saves tokens).
"""

import hashlib
import logging
from alfred.brain.api import Brain

log = logging.getLogger("alfred.intelligence.classifier")

_cache: dict[str, str] = {}


class Classifier:
    def __init__(self, brain: Brain):
        self.brain = brain

    def classify(self, text: str) -> str:
        """Classify a message. Returns URGENT/RESEARCH/IDEA/TASK/CHAT."""
        if not text or len(text.strip()) < 3:
            return "CHAT"

        msg_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        if msg_hash in _cache:
            log.debug(f"Cache hit: {_cache[msg_hash]}")
            return _cache[msg_hash]

        category = self.brain.classify(text)
        _cache[msg_hash] = category

        # Bound the cache at 10k entries
        if len(_cache) > 10_000:
            for k in list(_cache.keys())[:5_000]:
                del _cache[k]

        return category
