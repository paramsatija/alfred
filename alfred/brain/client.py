from typing import Optional

import anthropic
import logging
from alfred.config import Config
from alfred.brain.prompts import SYSTEM_PROMPT

log = logging.getLogger("alfred.brain")


class Brain:
    """Claude API wrapper with tiered model routing."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.tokens_used_today = 0

    def think(self, message, model=None, system=None, max_tokens=1024):
        """Send a message to Claude and get a response."""
        model = model or Config.MODEL_SONNET
        system = system or SYSTEM_PROMPT

        if self.tokens_used_today >= Config.DAILY_TOKEN_BUDGET:
            log.warning("Daily token budget exceeded")
            return "I've hit my daily token budget, sir. I'll be back at full capacity tomorrow. Only handling URGENT items now."

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": message}],
            )
            self.tokens_used_today += response.usage.input_tokens + response.usage.output_tokens
            log.info(f"Tokens used: {response.usage.input_tokens + response.usage.output_tokens} | Model: {model} | Daily total: {self.tokens_used_today}")
            return response.content[0].text
        except anthropic.RateLimitError:
            log.warning("Rate limited by Anthropic API, backing off")
            return "I'm being rate-limited right now, sir. I'll retry shortly."
        except anthropic.APIError as e:
            log.error(f"Anthropic API error: {e}")
            return "My brain hit an error. I've logged it. Try again in a moment."

    def classify(self, message):
        """Classify a message using Haiku (cheap)."""
        from alfred.brain.prompts import CLASSIFIER_PROMPT
        prompt = CLASSIFIER_PROMPT.format(message=message[:500])
        result = self.think(prompt, model=Config.MODEL_HAIKU, max_tokens=20)
        category = result.strip().upper()
        if category not in ("URGENT", "RESEARCH", "IDEA", "TASK", "CHAT"):
            category = "CHAT"
        return category

    def summarize_link(self, url, content):
        """Summarize link content using Sonnet."""
        from alfred.brain.prompts import LINK_SUMMARY_PROMPT
        prompt = LINK_SUMMARY_PROMPT.format(url=url, content=content[:8000])
        return self.think(prompt, model=Config.MODEL_SONNET, max_tokens=512)

    def generate_briefing(self, date, yesterday_summary, news, tasks, market):
        """Generate morning briefing using Sonnet."""
        from alfred.brain.prompts import BRIEFING_PROMPT
        prompt = BRIEFING_PROMPT.format(
            date=date,
            yesterday_summary=yesterday_summary or "No unprocessed messages from yesterday.",
            news=news or "No overnight news scanned yet.",
            tasks=tasks or "No pending tasks.",
            market=market or "Market data not configured yet.",
        )
        return self.think(prompt, model=Config.MODEL_SONNET, max_tokens=2048)

    def deep_research(self, topic, sources, date, requester):
        """Generate research report using Opus."""
        from alfred.brain.prompts import RESEARCH_PROMPT
        prompt = RESEARCH_PROMPT.format(
            topic=topic, sources=sources, date=date, requester=requester,
        )
        return self.think(prompt, model=Config.MODEL_OPUS, max_tokens=4096)

    def score_idea(self, idea):
        """Score a startup idea using Sonnet."""
        from alfred.brain.prompts import IDEA_SCORING_PROMPT
        prompt = IDEA_SCORING_PROMPT.format(idea=idea)
        return self.think(prompt, model=Config.MODEL_SONNET, max_tokens=512)

    def chat(self, message):
        """General conversation using Sonnet."""
        return self.think(message, model=Config.MODEL_SONNET, max_tokens=1024)

    def reset_daily_budget(self):
        """Reset token counter — called by midnight cron job."""
        log.info(f"Resetting daily token budget. Today's usage: {self.tokens_used_today}")
        self.tokens_used_today = 0
