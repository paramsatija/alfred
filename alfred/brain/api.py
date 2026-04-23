"""Regular Claude API calls — classification, chat, scoring, web search.

Prompt caching: applied only for Sonnet calls (system prompt > 2048 tokens
after formatting). Haiku's minimum cacheable length is 4096 tokens —
our system prompt is too short, so we skip caching for Haiku to avoid
wasting the cache_control header.

Web search: implements the full tool use loop. Claude may request multiple
searches before producing a final text response. We loop until Claude
stops requesting tools or hits max iterations.
"""

import logging
import threading
import anthropic
from alfred.config import Config
from alfred.brain.prompts import (
    SYSTEM_PROMPT,
    CLASSIFIER_PROMPT,
    LINK_SUMMARY_PROMPT,
    IDEA_SCORING_PROMPT,
)

log = logging.getLogger("alfred.brain.api")

# Shared token counter — accessed by both Brain and agent sessions
_token_lock = threading.Lock()
_tokens_used_today = 0


def get_tokens_used() -> int:
    return _tokens_used_today


def add_tokens(count: int):
    global _tokens_used_today
    with _token_lock:
        _tokens_used_today += count


def reset_tokens():
    global _tokens_used_today
    with _token_lock:
        log.info(f"Resetting daily token budget. Today's usage: {_tokens_used_today}")
        _tokens_used_today = 0


def is_over_budget() -> bool:
    return _tokens_used_today >= Config.DAILY_TOKEN_BUDGET


class Brain:
    """Anthropic messages API with prompt caching and tool use loop."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def _call(
        self,
        message: str,
        model: str = None,
        system: str = None,
        max_tokens: int = 1024,
    ) -> str:
        """Single-turn API call. Prompt caching applied for Sonnet only."""
        model = model or Config.MODEL_SONNET
        system = system or SYSTEM_PROMPT

        if is_over_budget():
            log.warning("Daily token budget exceeded")
            return (
                "I've hit my daily token budget, Batman. "
                "I'll be back at full capacity tomorrow."
            )

        try:
            kwargs = dict(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": message}],
            )
            # Only cache for Sonnet+ (Haiku needs 4096+ tokens to cache)
            if model != Config.MODEL_HAIKU:
                kwargs["cache_control"] = {"type": "ephemeral"}

            response = self.client.messages.create(**kwargs)

            usage = response.usage
            total = usage.input_tokens + usage.output_tokens
            add_tokens(total)

            cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
            if cache_read > 0:
                log.info(f"Tokens: {total} (cache hit: {cache_read}) | {model}")
            else:
                log.info(f"Tokens: {total} | {model} | Daily: {get_tokens_used()}")

            return response.content[0].text

        except anthropic.RateLimitError:
            log.warning("Rate limited by Anthropic API")
            return "I'm being rate-limited right now, Batman. I'll retry shortly."
        except anthropic.APIError as e:
            log.error(f"Anthropic API error: {e}")
            return "My brain hit an error. I've logged it. Try again in a moment."

    def _call_with_search(self, message: str, max_tokens: int = 2048) -> str:
        """Call Claude with web_search tool, handling the full tool use loop.

        Claude may request 1+ searches before producing a final answer.
        We loop: send request → if Claude wants to search → feed results
        back → repeat until Claude produces a text response or we hit
        max iterations.
        """
        if is_over_budget():
            return "Daily token budget exceeded, Batman."

        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
        messages = [{"role": "user", "content": message}]
        max_loops = 6

        try:
            for loop in range(max_loops):
                response = self.client.messages.create(
                    model=Config.MODEL_SONNET,
                    max_tokens=max_tokens,
                    cache_control={"type": "ephemeral"},
                    system=SYSTEM_PROMPT,
                    tools=tools,
                    messages=messages,
                )

                usage = response.usage
                add_tokens(usage.input_tokens + usage.output_tokens)

                # If Claude is done (no more tool calls), extract text
                if response.stop_reason == "end_turn":
                    parts = []
                    for block in response.content:
                        if hasattr(block, "text"):
                            parts.append(block.text)
                    return "\n".join(parts) if parts else "No response generated."

                # If Claude wants to use tools, add the assistant turn and
                # a synthetic tool result turn so it can continue.
                # For server-side tools like web_search, the API handles
                # execution internally — we just need to pass back the
                # full response cycle.
                if response.stop_reason == "tool_use":
                    # Append assistant turn with all content blocks
                    messages.append({"role": "assistant", "content": response.content})

                    # Build tool results for each tool_use block
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": "Search completed.",
                            })

                    if tool_results:
                        messages.append({"role": "user", "content": tool_results})
                    continue

                # Unknown stop reason — break
                break

            # Fell through the loop — extract whatever text we have
            parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    parts.append(block.text)
            return "\n".join(parts) if parts else "Research completed but no summary was generated."

        except anthropic.APIError as e:
            log.error(f"API error (web search loop): {e}")
            return f"Research hit an error: {e}"

    # ── Public methods ───────────────────────────────────────────────────

    def classify(self, message: str) -> str:
        """Classify using Haiku. No caching (prompt too short for Haiku's 4096 min)."""
        prompt = CLASSIFIER_PROMPT.format(message=message[:500])
        result = self._call(prompt, model=Config.MODEL_HAIKU, max_tokens=20)
        category = result.strip().upper()
        valid = {"URGENT", "RESEARCH", "IDEA", "TASK", "CHAT"}
        return category if category in valid else "CHAT"

    def chat(self, message: str, thread_history: list = None) -> str:
        """Conversation with optional thread history for multi-turn context."""
        if not thread_history:
            return self._call(message, max_tokens=1024)

        if is_over_budget():
            return "Daily token budget exceeded, Batman."

        # Multi-turn: send full conversation history
        messages = list(thread_history)
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.messages.create(
                model=Config.MODEL_SONNET,
                max_tokens=1024,
                cache_control={"type": "ephemeral"},
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            add_tokens(response.usage.input_tokens + response.usage.output_tokens)
            return response.content[0].text
        except anthropic.APIError as e:
            log.error(f"Chat error: {e}")
            return "Something went wrong with my response."

    def summarize_link(self, url: str, content: str) -> str:
        prompt = LINK_SUMMARY_PROMPT.format(url=url, content=content[:8000])
        return self._call(prompt, max_tokens=512)

    def score_idea(self, idea: str) -> str:
        prompt = IDEA_SCORING_PROMPT.format(idea=idea)
        return self._call(prompt, max_tokens=512)

    def quick_research(self, query: str) -> str:
        """Light research with web search tool loop."""
        return self._call_with_search(
            f"Research this for Batman and give a concise summary with sources: {query}",
            max_tokens=2048,
        )

    def generate_briefing(self, date: str, memory_context: str, topics: str) -> str:
        """Generate a briefing using web search (fallback when no Managed Agent)."""
        from alfred.brain.prompts import BRIEFING_TASK_TEMPLATE
        task = BRIEFING_TASK_TEMPLATE.format(
            date=date, memory_context=memory_context, topics=topics,
        )
        return self._call_with_search(task, max_tokens=4096)
