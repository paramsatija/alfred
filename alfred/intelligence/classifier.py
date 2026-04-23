from typing import Dict

import hashlib
import logging
from alfred.brain.client import Brain

log = logging.getLogger("alfred.intelligence.classifier")

# Simple in-memory dedup cache (per session)
_seen: Dict[str, str] = {}


class Classifier:
    """Classifies messages using Claude Haiku (cheap and fast)."""

    def __init__(self, brain: Brain):
        self.brain = brain

    def classify(self, text: str) -> str:
        """Classify a message. Returns: URGENT, RESEARCH, IDEA, TASK, or CHAT."""
        if not text or len(text.strip()) < 3:
            return "CHAT"

        # Check dedup cache
        msg_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        if msg_hash in _seen:
            log.info(f"Duplicate message detected, returning cached: {_seen[msg_hash]}")
            return _seen[msg_hash]

        category = self.brain.classify(text)
        _seen[msg_hash] = category

        # Keep cache bounded
        if len(_seen) > 10000:
            # Remove oldest half
            keys = list(_seen.keys())
            for k in keys[:5000]:
                del _seen[k]

        return category
