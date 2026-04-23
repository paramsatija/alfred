"""Research engine — orchestrates search, fetch, and synthesis."""

import logging
from datetime import datetime
from alfred.brain.client import Brain
from alfred.research.web_search import search, search_news
from alfred.intelligence.link_processor import LinkProcessor
from alfred.memory.store import MemoryStore

log = logging.getLogger("alfred.research")


class ResearchEngine:
    def __init__(self, brain: Brain, link_processor: LinkProcessor, memory: MemoryStore):
        self.brain = brain
        self.link_processor = link_processor
        self.memory = memory

    def deep_research(self, topic: str, requester: str = "sir") -> str:
        """Run a deep research session on a topic."""
        log.info(f"Starting deep research on: {topic}")

        # Search for the topic from multiple angles
        results = search(topic, count=10)
        news = search_news(topic, count=5)
        all_results = results + news

        if not all_results:
            return f"I couldn't find any results for '{topic}'. The search API might be down, or try rephrasing the query."

        # Fetch and summarize top results
        sources_text = []
        for r in all_results[:8]:  # Limit to 8 sources to manage tokens
            title = r["title"]
            url = r["url"]
            desc = r["description"]
            sources_text.append(f"**{title}**\nURL: {url}\n{desc}\n")

        sources_combined = "\n---\n".join(sources_text)

        # Generate research report using Opus
        report = self.brain.deep_research(
            topic=topic,
            sources=sources_combined,
            date=datetime.now().strftime("%Y-%m-%d"),
            requester=requester,
        )

        # Save to memory
        urls = [r["url"] for r in all_results[:8]]
        self.memory.add_research(topic, report[:500], urls)
        for url in urls:
            self.memory.add_seen_url(url)

        return report

    def scan_topics(self) -> str:
        """Scan all configured topics for overnight news. Used by morning briefing."""
        topics = self.memory.get_topics()
        all_news = []

        for topic in topics:
            results = search_news(topic, count=3)
            for r in results:
                if not self.memory.has_seen_url(r["url"]):
                    all_news.append(f"[{topic}] {r['title']}: {r['description']}")
                    self.memory.add_seen_url(r["url"])

        if not all_news:
            return "No new developments overnight across your tracked topics."

        return "\n".join(all_news[:15])  # Cap at 15 items
