"""Morning briefing generator.

Primary: Managed Agent session (deep, multi-search).
Fallback: Brain.generate_briefing via web_search tool (lighter but still useful).
"""

import logging
from datetime import datetime
from alfred.brain import agent as managed_agent
from alfred.brain.api import Brain
from alfred.brain.prompts import BRIEFING_TASK_TEMPLATE
from alfred.config import Config
from alfred.memory.store import MemoryStore
from alfred.slack.senders import post_briefing

log = logging.getLogger("alfred.briefing")


class BriefingGenerator:
    def __init__(self, brain: Brain, memory: MemoryStore):
        self.brain = brain
        self.memory = memory

    def generate_and_post(self):
        """Generate the morning briefing and post to Slack.

        Uses Managed Agent if configured, otherwise falls back to
        Brain.generate_briefing which uses the web_search tool loop.
        """
        today = datetime.now().strftime("%A, %B %d, %Y")
        memory_context = self.memory.get_briefing_context()
        topics = ", ".join(self.memory.get_topics())

        if Config.has_agent():
            log.info("Generating morning briefing via agent session...")
            task = BRIEFING_TASK_TEMPLATE.format(
                date=today, memory_context=memory_context, topics=topics,
            )
            briefing = managed_agent.run_session(task)
        else:
            log.info("Generating morning briefing via API (no Managed Agent)...")
            briefing = self.brain.generate_briefing(today, memory_context, topics)

        post_briefing(briefing)
        log.info("Morning briefing posted to #daily-briefing")
        return briefing
