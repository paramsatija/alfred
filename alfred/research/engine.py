"""Research engine — powered by Claude Managed Agent sessions.

Deep research fires a full agent session with web_search + web_fetch.
The agent autonomously searches, reads pages, and synthesizes a report.
No more manual Brave Search + httpx + BeautifulSoup pipeline.
"""

import logging
from datetime import datetime
from alfred.brain import agent as managed_agent
from alfred.brain.api import Brain
from alfred.brain.prompts import RESEARCH_TASK_TEMPLATE
from alfred.memory.store import MemoryStore

log = logging.getLogger("alfred.research")


class ResearchEngine:
    def __init__(self, brain: Brain, memory: MemoryStore):
        self.brain = brain
        self.memory = memory

    def deep_research(self, topic: str, requester: str = "Batman") -> str:
        """Run a full research session using the Managed Agent.

        The agent has web_search and web_fetch — it autonomously searches
        from multiple angles, reads pages, and produces a structured report.
        """
        log.info(f"Starting deep research: {topic}")

        task = RESEARCH_TASK_TEMPLATE.format(
            topic=topic,
            date=datetime.now().strftime("%Y-%m-%d"),
            requester=requester,
        )

        report = managed_agent.run_session(task)

        self.memory.add_research(topic, report[:500], [])
        log.info(f"Deep research complete: {topic}")
        return report

    def quick_research(self, query: str) -> str:
        """Lighter research using web_search tool in a regular API call.

        Good for quick questions that don't need a full agent session.
        """
        log.info(f"Quick research: {query}")
        return self.brain.quick_research(query)
