"""Link processor — fetches URLs and summarizes them.

Uses httpx + BeautifulSoup for direct URL fetching (fast, free).
Falls back to Brain.quick_research (web_search tool) when a page
can't be fetched directly (paywall, JS-heavy, broken).
"""

import hashlib
import logging
import httpx
from bs4 import BeautifulSoup
from alfred.brain.api import Brain

log = logging.getLogger("alfred.intelligence.link_processor")

_url_cache: dict[str, str] = {}


class LinkProcessor:
    def __init__(self, brain: Brain):
        self.brain = brain

    def process(self, url: str) -> str:
        """Fetch a URL, extract text, and summarize. Falls back to web search."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        if url_hash in _url_cache:
            log.info(f"URL cache hit: {url}")
            return _url_cache[url_hash]

        content = self._fetch(url)

        if content:
            summary = self.brain.summarize_link(url, content)
        else:
            # Fallback: let Claude search for the topic instead
            log.info(f"Direct fetch failed for {url}, falling back to web search")
            summary = self.brain.quick_research(
                f"I couldn't fetch this URL directly: {url}\n"
                "Search for the same topic and summarize what you find. "
                "Mention that the original link was inaccessible."
            )

        _url_cache[url_hash] = summary
        if len(_url_cache) > 500:
            for k in list(_url_cache.keys())[:250]:
                del _url_cache[k]

        return summary

    def _fetch(self, url: str) -> str | None:
        """Fetch URL content and extract readable text."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko)"
            ),
        }
        try:
            with httpx.Client(follow_redirects=True, timeout=15.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "application/pdf" in content_type:
                    return "[PDF detected — PDF parsing coming in a future phase]"

                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                if len(text) > 10_000:
                    text = text[:10_000] + "\n[...truncated]"

                return text if len(text) > 50 else None

        except httpx.TimeoutException:
            log.warning(f"Timeout fetching {url}")
        except httpx.HTTPStatusError as e:
            log.warning(f"HTTP {e.response.status_code} fetching {url}")
        except Exception as e:
            log.error(f"Error fetching {url}: {e}")
        return None
