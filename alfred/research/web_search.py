"""Brave Search API integration for web research."""

from typing import Dict, List

import logging
import httpx
from alfred.config import Config

log = logging.getLogger("alfred.research.search")

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def search(query: str, count: int = 5) -> List[Dict]:
    """Search the web using Brave Search API.

    Returns list of: {"title": ..., "url": ..., "description": ...}
    """
    if not Config.BRAVE_SEARCH_API_KEY:
        log.warning("Brave Search API key not configured")
        return []

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": Config.BRAVE_SEARCH_API_KEY,
    }
    params = {"q": query, "count": count}

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                })
            return results

    except Exception as e:
        log.error(f"Brave Search error: {e}")
        return []


def search_news(topic: str, count: int = 5) -> List[Dict]:
    """Search for recent news on a topic."""
    return search(f"{topic} latest news 2026", count=count)
