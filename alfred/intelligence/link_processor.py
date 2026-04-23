from typing import Dict, Optional

import hashlib
import logging
import httpx
from bs4 import BeautifulSoup
from alfred.brain.client import Brain

log = logging.getLogger("alfred.intelligence.link_processor")

_url_cache: Dict[str, str] = {}


class LinkProcessor:
    """Fetches URLs, extracts content, and summarizes via Claude."""

    def __init__(self, brain: Brain):
        self.brain = brain

    def process(self, url):
        """Fetch a URL, extract text, and summarize it."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        if url_hash in _url_cache:
            log.info(f"URL cache hit: {url}")
            return _url_cache[url_hash]

        content = self._fetch(url)
        if not content:
            return f"Couldn't fetch the link: {url}\nIt might be paywalled, broken, or requires JavaScript."

        summary = self.brain.summarize_link(url, content)

        _url_cache[url_hash] = summary
        if len(_url_cache) > 500:
            keys = list(_url_cache.keys())
            for k in keys[:250]:
                del _url_cache[k]

        return summary

    def _fetch(self, url):
        """Fetch URL content and extract readable text."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }
        try:
            with httpx.Client(follow_redirects=True, timeout=15.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")

                if "application/pdf" in content_type:
                    return "[PDF detected - PDF parsing available in Phase 2]"

                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                if len(text) > 10000:
                    text = text[:10000] + "\n[...truncated]"

                return text if len(text) > 50 else None

        except httpx.TimeoutException:
            log.warning(f"Timeout fetching {url}")
            return None
        except httpx.HTTPStatusError as e:
            log.warning(f"HTTP error fetching {url}: {e.response.status_code}")
            return None
        except Exception as e:
            log.error(f"Error fetching {url}: {e}")
            return None
