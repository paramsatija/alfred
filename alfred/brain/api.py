"""Regular Claude API calls — classification, chat, scoring.

Uses prompt caching (cache_control) so the system prompt is cached
across calls. Cache reads cost 10% of base input price — massive
savings when the same system prompt is sent hundreds of times/day.

Tier 1: Haiku for classification (no tools, dirt cheap)
Tier 2: Sonnet for chat/scoring/summaries (no tools or web_search)
"""

import logging
import anthropic
from alfred.config import Config
from alfred.brain.prompts import (
    SYSTEM_PROMPT,
    CLASSIFIER_PROMPT,
    LINK_SUMMARY_PROMPT,
    IDEA_SCORING_PROMPT,
)

log = logging.getLogger("alfred.brain.api")


class Brain:
    """Thin wrapper around the Anthropic messages API with prompt caching."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.tokens_used_today = 0

    def _call(
        self,
        message: str,
        model: str = None,
        system: str = None,
        max_tokens: int = 1024,
    ) -> str:
        """Send a message to Claude with automatic prompt caching.

        The system prompt is cached for 5 minutes by default. Subsequent
        calls within that window read from cache at 10% of input cost.
        """
        model = model or Config.MODEL_SONNET
        system = system or SYSTEM_PROMPT

        if self.tokens_used_today >= Config.DAILY_TOKEN_BUDGET:
            log.warning("Daily token budget exceeded")
            return (
                "I've hit my daily token budget, Batman. "
                "I'll be back at full capacity tomorrow. Only handling URGENT items now."
            )

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                # Automatic prompt caching — system prompt cached across calls
                cache_control={"type": "ephemeral"},
                system=system,
                messages=[{"role": "user", "content": message}],
            )

            usage = response.usage
            total = usage.input_tokens + usage.output_tokens
            self.tokens_used_today += total

            # Log cache performance
            cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
            cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
            if cache_read > 0:
                log.info(f"Tokens: {total} (cache hit: {cache_read}) | Model: {model}")
            elif cache_write > 0:
                log.info(f"Tokens: {total} (cache write: {cache_write}) | Model: {model}")
            else:
                log.info(f"Tokens: {total} | Model: {model} | Daily: {self.tokens_used_today}")

            return response.content[0].text

        except anthropic.RateLimitError:
            log.warning("Rate limited by Anthropic API")
            return "I'm being rate-limited right now, Batman. I'll retry shortly."
        except anthropic.APIError as e:
            log.error(f"Anthropic API error: {e}")
            return "My brain hit an error. I've logged it. Try again in a moment."

    def _call_with_search(self, message: str, max_tokens: int = 2048) -> str:
        """Call Claude with native web_search tool + prompt caching.

        Claude autonomously decides when to search. Replaces the entire
        Brave Search + manual fetch pipeline from the old architecture.
        """
        if self.tokens_used_today >= Config.DAILY_TOKEN_BUDGET:
            return "Daily token budget exceeded, Batman."

        try:
            response = self.client.messages.create(
                model=Config.MODEL_SONNET,
                max_tokens=max_tokens,
                cache_control={"type": "ephemeral"},
                system=SYSTEM_PROMPT,
                tools=[
                    {"type": "web_search_20260209", "name": "web_search", "max_uses": 5},
                ],
                messages=[{"role": "user", "content": message}],
            )

            usage = response.usage
            total = usage.input_tokens + usage.output_tokens
            self.tokens_used_today += total

            cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
            log.info(f"Tokens (search): {total} (cache hit: {cache_read}) | Daily: {self.tokens_used_today}")

            parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    parts.append(block.text)
            return "\n".join(parts) if parts else "No response generated."

        except anthropic.APIError as e:
            log.error(f"API error (web search): {e}")
            return "Research hit an error. I've logged it."

    # ── Public methods ───────────────────────────────────────────────────

    def classify(self, message: str) -> str:
        """Classify a message using Haiku. Returns URGENT/RESEARCH/IDEA/TASK/CHAT."""
        prompt = CLASSIFIER_PROMPT.format(message=message[:500])
        result = self._call(prompt, model=Config.MODEL_HAIKU, max_tokens=20)
        category = result.strip().upper()
        valid = {"URGENT", "RESEARCH", "IDEA", "TASK", "CHAT"}
        return category if category in valid else "CHAT"

    def chat(self, message: str) -> str:
        """General conversation using Sonnet."""
        return self._call(message, max_tokens=1024)

    def summarize_link(self, url: str, content: str) -> str:
        """Summarize fetched link content."""
        prompt = LINK_SUMMARY_PROMPT.format(url=url, content=content[:8000])
        return self._call(prompt, max_tokens=512)

    def score_idea(self, idea: str) -> str:
        """Score a startup idea."""
        prompt = IDEA_SCORING_PROMPT.format(idea=idea)
        return self._call(prompt, max_tokens=512)

    def quick_research(self, query: str) -> str:
        """Light research with web search — when a full agent session is overkill."""
        return self._call_with_search(
            f"Research this for Batman and give a concise summary with sources: {query}",
            max_tokens=2048,
        )

    def reset_daily_budget(self):
        """Reset token counter — called by midnight cron job."""
        log.info(f"Resetting daily token budget. Today's usage: {self.tokens_used_today}")
        self.tokens_used_today = 0
