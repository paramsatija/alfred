"""Morning briefing generator — powered by Managed Agent.

The agent session searches all tracked topics, gathers overnight news,
and synthesizes a personalized briefing.
"""

import logging
from datetime import datetime
from alfred.brain import agent as managed_agent
from alfred.brain.prompts import BRIEFING_TASK_TEMPLATE
from alfred.memory.store import MemoryStore
from alfred.slack.senders import post_briefing

log = logging.getLogger("alfred.briefing")


class BriefingGenerator:
    def __init__(self, memory: MemoryStore):
        self.memory = memory

    def generate_and_post(self):
        """Generate the morning briefing via a Managed Agent session and post to Slack."""
        log.info("Generating morning briefing via agent session...")

        today = datetime.now().strftime("%A, %B %d, %Y")
        memory_context = self.memory.get_briefing_context()
        topics = ", ".join(self.memory.get_topics())

        task = BRIEFING_TASK_TEMPLATE.format(
            date=today,
            memory_context=memory_context,
            topics=topics,
        )

        briefing = managed_agent.run_session(task)

        post_briefing(briefing)
        log.info("Morning briefing posted to #daily-briefing")
        return briefing
