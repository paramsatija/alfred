"""Persistent memory — JSON file store with built-in deduplication.

Stores preferences, research history, seen URLs, ideas, and tasks.
Uses a threading lock + atomic writes to prevent corruption from
concurrent Slack event handlers.
"""

import hashlib
import json
import os
import tempfile
import time
import threading
import logging
from alfred.config import Config

log = logging.getLogger("alfred.memory")

MEMORY_FILE = os.path.join(Config.DATA_DIR, "memory.json")

_DEFAULTS = {
    "users": {},
    "research_history": [],
    "seen_urls": [],
    "seen_hashes": {},
    "preferences": {
        "wake_time": Config.WAKE_TIME,
        "timezone": Config.TIMEZONE,
        "topics": [
            "fertilizers",
            "agriculture",
            "agritech",
            "tech startups",
            "AI",
            "science breakthroughs",
            "India agriculture policy",
        ],
    },
    "ideas": [],
    "tasks": [],
}


class MemoryStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
                for key, default in _DEFAULTS.items():
                    data.setdefault(key, default)
                return data
            except (json.JSONDecodeError, IOError):
                log.warning("Corrupted memory file, starting fresh")
        return dict(_DEFAULTS)

    def _save(self):
        """Atomic write: write to temp file then rename (prevents corruption)."""
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(MEMORY_FILE), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp_path, MEMORY_FILE)
        except Exception:
            os.unlink(tmp_path)
            raise

    # ── Generic key-value ────────────────────────────────────────────────

    def remember(self, key: str, value):
        with self._lock:
            self._data[key] = value
            self._save()

    def recall(self, key: str, default=None):
        return self._data.get(key, default)

    # ── Deduplication (check-only vs. check-and-mark) ────────────────────

    def is_duplicate(self, content: str, ttl_hours: int = 24) -> bool:
        """Check if content was seen recently. Does NOT register it.

        Call mark_seen() after successfully processing the message
        so legitimate retries aren't swallowed.
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        seen = self._data.get("seen_hashes", {})

        if content_hash in seen:
            if time.time() - seen[content_hash] < ttl_hours * 3600:
                return True
        return False

    def mark_seen(self, content: str):
        """Register content as processed. Call after successful handling."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        with self._lock:
            self._data["seen_hashes"][content_hash] = time.time()
            self._prune_hashes()
            self._save()

    def _prune_hashes(self):
        cutoff = time.time() - 48 * 3600
        self._data["seen_hashes"] = {
            k: v for k, v in self._data["seen_hashes"].items() if v > cutoff
        }

    # ── Research ─────────────────────────────────────────────────────────

    def add_research(self, topic: str, summary: str, urls: list[str]):
        with self._lock:
            entry = {"topic": topic, "summary": summary[:500], "urls": urls, "ts": time.time()}
            self._data["research_history"].append(entry)
            self._data["research_history"] = self._data["research_history"][-100:]
            self._save()

    # ── URLs ─────────────────────────────────────────────────────────────

    def add_seen_url(self, url: str):
        with self._lock:
            if url not in self._data["seen_urls"]:
                self._data["seen_urls"].append(url)
                self._data["seen_urls"] = self._data["seen_urls"][-1000:]
                self._save()

    def has_seen_url(self, url: str) -> bool:
        return url in self._data["seen_urls"]

    # ── Ideas ────────────────────────────────────────────────────────────

    def add_idea(self, idea: str, score: str):
        with self._lock:
            self._data["ideas"].append({"idea": idea[:200], "score": score, "ts": time.time()})
            self._save()

    # ── Topics ───────────────────────────────────────────────────────────

    def get_topics(self) -> list[str]:
        return self._data.get("preferences", {}).get("topics", [])

    # ── Briefing context ─────────────────────────────────────────────────

    def get_briefing_context(self) -> str:
        ideas = self._data.get("ideas", [])[-5:]
        research = self._data.get("research_history", [])[-5:]

        parts = []
        if ideas:
            parts.append("Recent ideas:\n" + "\n".join(f"- {i['idea']}" for i in ideas))
        if research:
            parts.append("Recent research:\n" + "\n".join(f"- {r['topic']}" for r in research))
        return "\n\n".join(parts) if parts else "No recent activity to report."
