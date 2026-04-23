"""Simple persistent memory using JSON files.

Stores user preferences, research history, and learned patterns.
Lightweight — no database needed for Phase 1-3.
Can be upgraded to Memory MCP knowledge graph later.
"""

from typing import List

import json
import os
import logging
from alfred.config import Config

log = logging.getLogger("alfred.memory")

MEMORY_FILE = os.path.join(Config.DATA_DIR, "memory.json")


class MemoryStore:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                log.warning("Corrupted memory file, starting fresh")
        return {
            "users": {},
            "research_history": [],
            "seen_urls": [],
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

    def _save(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def remember(self, key: str, value):
        """Store a key-value pair."""
        self._data[key] = value
        self._save()

    def recall(self, key: str, default=None):
        """Retrieve a stored value."""
        return self._data.get(key, default)

    def add_research(self, topic: str, summary: str, urls: List[str]):
        """Log a completed research task."""
        entry = {"topic": topic, "summary": summary[:500], "urls": urls}
        self._data["research_history"].append(entry)
        # Keep last 100 research entries
        self._data["research_history"] = self._data["research_history"][-100:]
        self._save()

    def add_seen_url(self, url: str):
        """Mark a URL as processed."""
        if url not in self._data["seen_urls"]:
            self._data["seen_urls"].append(url)
            # Keep last 1000 URLs
            self._data["seen_urls"] = self._data["seen_urls"][-1000:]
            self._save()

    def has_seen_url(self, url: str) -> bool:
        """Check if a URL has been processed before."""
        return url in self._data["seen_urls"]

    def add_idea(self, idea: str, score: str):
        """Save a scored idea."""
        self._data["ideas"].append({"idea": idea[:200], "score": score})
        self._save()

    def get_topics(self) -> List[str]:
        """Get configured research topics."""
        return self._data.get("preferences", {}).get("topics", [])

    def get_unprocessed_summary(self) -> str:
        """Get summary of recent unprocessed items for briefing."""
        ideas = self._data.get("ideas", [])[-5:]
        research = self._data.get("research_history", [])[-5:]

        parts = []
        if ideas:
            parts.append("Recent ideas:\n" + "\n".join(f"- {i['idea']}" for i in ideas))
        if research:
            parts.append("Recent research:\n" + "\n".join(f"- {r['topic']}" for r in research))
        return "\n\n".join(parts) if parts else "No recent activity."
