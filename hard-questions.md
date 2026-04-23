I've read every critical file. Here are 10 hard questions — real problems I found in the code, not hypothetical ones.

---

## 10 Hard Questions About ALFRED

### 1. The Slack bot is BLOCKING during agent sessions — will it freeze?

`bot.py` line 112: `research_engine.deep_research(text)` calls `run_session()` which streams events synchronously. A Managed Agent session can take **60-120 seconds** for deep research. During that time, **Slack Bolt's event handler is blocked**. If two people send research requests at the same time, the second one waits until the first finishes. If enough messages queue up, Slack will **retry delivery** and you'll get duplicate processing. There's no threading or async here.

**Verdict: This will break under any real usage.**

### 2. Prompt caching won't actually work for Haiku classification.

The docs you shared say minimum cacheable length is **4096 tokens for Haiku 4.5**. Your `SYSTEM_PROMPT` in `prompts.py` is ~200 words / ~300 tokens. That's nowhere near 4096. Every single Haiku classification call will **silently fail to cache** — no error, just no savings. The `cache_control={"type": "ephemeral"}` is being sent and ignored on 80% of your API calls.

**Verdict: Prompt caching is a no-op for your most frequent call type.**

### 3. `_call_with_search` doesn't handle the tool use loop.

`api.py` line 96: When you add the `web_search` tool, Claude may respond with a `tool_use` block (requesting a search), not a text block. The Messages API with tools requires a **multi-turn loop** — Claude says "I want to search X", you get the results, you send them back, Claude responds with text. Your code does a single `messages.create()` and just extracts text blocks. If Claude decides to search, **you'll get an empty response** because the text comes AFTER the tool results are processed.

**Verdict: Web search in regular API calls is broken. It will return empty or partial responses.**

### 4. Token budget doesn't track Managed Agent sessions.

`Brain.tokens_used_today` tracks tokens from regular API calls. But `agent.py` line 98 creates a **separate** `anthropic.Anthropic()` client and runs sessions through it. Those sessions consume tokens but **none of that usage is counted** against `tokens_used_today`. The midnight reset and budget gate in `brain/api.py` have no idea how many tokens the agent sessions burned. You could blow through your Anthropic bill with agent sessions while the budget counter says you're at 10%.

**Verdict: Your cost protection has a massive blind spot.**

### 5. Memory store has a race condition on concurrent writes.

`store.py`: `_save()` does `json.dump()` to `memory.json`. If two Slack messages arrive near-simultaneously (both trigger `is_duplicate` → both call `_save()`), one write will clobber the other. There's no file lock, no atomic write. On Railway with a single process this is less likely, but Slack Bolt processes events in threads — so it **can** happen.

**Verdict: Data loss possible under concurrent messages.**

### 6. The `is_duplicate` check has a side effect that silently drops messages.

`bot.py` line 76: `memory.is_duplicate(text)` is called for EVERY message. But look at `store.py` line 85: `is_duplicate` **registers the hash even if it returns False** (first time seeing it). This means if someone sends "check urea prices" and then 5 minutes later sends "check urea prices" again (legitimately wanting a fresh check), ALFRED will silently ignore the second one for 24 hours. The user will have zero feedback that their message was dropped.

**Verdict: Legitimate repeat requests get silently swallowed.**

### 7. The `App(token=Config.SLACK_BOT_TOKEN)` runs at module import time.

`bot.py` line 19: `app = App(token=Config.SLACK_BOT_TOKEN)` executes when the module is **imported**, not when `start()` is called. If `SLACK_BOT_TOKEN` is empty at import time (before `Config.validate()` runs in `main.py`), this could silently create a broken App object. Python's import order matters — `main.py` imports `slack.bot` on line 29, but `Config.validate()` doesn't run until line 41.

**Verdict: Potential for a silent misconfiguration that only surfaces at runtime.**

### 8. No conversation context — ALFRED has no memory of the thread it's in.

`bot.py` sends every message to `brain.chat(text)` as a **single-turn** conversation. If Batman says "research urea prices" and ALFRED responds, then Batman says "tell me more about point 3", ALFRED has **zero context** about what "point 3" was. Every message is a fresh conversation with no history. The morning briefing says "Reply with a number to deep-dive" but there's no handler for the follow-up.

**Verdict: The interactive briefing flow advertised in GAMEPLAN.md doesn't work.**

### 9. `web_search_20260209` tool — the version string might be wrong.

You're using `"type": "web_search_20260209"` in `api.py`. This is a versioned tool type. If Anthropic has updated this to a newer version, or if your SDK version (`anthropic>=0.52.0`) expects a different tool type string, every web search call will fail. We pulled this from docs but haven't actually **tested** it against the live API.

**Verdict: Untested API integration — could fail on first real call.**

### 10. The morning briefing has no fallback if the Managed Agent isn't set up.

`briefing/generator.py` calls `managed_agent.run_session(task)` directly. If `ALFRED_AGENT_ID` is empty, `run_session` returns a string saying "Managed Agent not configured." That string gets **posted to `#daily-briefing`** as the actual morning briefing. Every morning at 10:00 AM, your briefing channel gets "Managed Agent not configured. Run python -m alfred.setup_agent first." There's no fallback to `brain.quick_research()` like the Slack bot has.

**Verdict: Without the agent, your daily briefing is broken.**

---

## Summary: What Actually Works vs. What Doesn't

| Component | Status |
|-----------|--------|
| Slack listener + classification | Works |
| Chat responses | Works (but no context) |
| Idea scoring | Works |
| Link processing (httpx + BS4) | Works |
| Web search fallback in links | Broken (no tool use loop) |
| Quick research via API | Broken (no tool use loop) |
| Deep research via agent | Probably works but blocks the bot |
| Morning briefing | Broken without agent, blocks scheduler thread |
| Prompt caching | Only works for Sonnet calls, not Haiku |
| Token budget | Doesn't track agent sessions |
| Dedup | Works but too aggressive |
| Memory persistence | Works but race condition possible |

Want me to fix these? I'd prioritize: (1) the blocking issue, (2) the web search tool loop, (3) the briefing fallback, and (4) conversation context. Those four would make ALFRED actually functional end-to-end.