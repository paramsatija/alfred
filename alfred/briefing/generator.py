"""Morning briefing generator."""

import logging
from datetime import datetime
from alfred.brain.client import Brain
from alfred.research.engine import ResearchEngine
from alfred.memory.store import MemoryStore
from alfred.slack.senders import post_briefing

log = logging.getLogger("alfred.briefing")


class BriefingGenerator:
    def __init__(self, brain: Brain, research: ResearchEngine, memory: MemoryStore):
        self.brain = brain
        self.research = research
        self.memory = memory

    def generate_and_post(self):
        """Generate the morning briefing and post to Slack."""
        log.info("Generating morning briefing...")

        today = datetime.now().strftime("%A, %B %d, %Y")

        # Collect data for briefing
        yesterday_summary = self.memory.get_unprocessed_summary()
        overnight_news = self.research.scan_topics()
        tasks = "No pending tasks."  # Task system comes in Phase 5
        market = "Market data not configured yet."  # Comes in Phase 6

        # Generate briefing
        briefing = self.brain.generate_briefing(
            date=today,
            yesterday_summary=yesterday_summary,
            news=overnight_news,
            tasks=tasks,
            market=market,
        )

        # Post to Slack
        post_briefing(briefing)
        log.info("Morning briefing posted to #daily-briefing")
        return briefing
