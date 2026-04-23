"""Slack bot — event handlers for messages and mentions.

Key fixes applied:
  - App() is created lazily (not at import time) to avoid empty-token init
  - Heavy tasks (research, agent sessions) run in background threads
  - Thread history tracked per conversation for multi-turn context
  - Dedup uses check-then-mark pattern (mark only after successful handling)

Routing logic:
  CHAT     → ignore (unless @ALFRED mentioned → quick chat)
  URGENT   → brain.chat with urgency framing → reply in thread
  RESEARCH → links: LinkProcessor | no links: ResearchEngine
  IDEA     → brain.score_idea → reply in thread
  TASK     → brain.chat with task framing → reply in thread
"""

import logging
import re
import threading
import time
from collections import defaultdict
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from alfred.config import Config

log = logging.getLogger("alfred.slack")

# Lazy-initialized in start() — prevents empty-token crash at import time
app: App | None = None

# Dependencies injected by main.py
brain = None
classifier = None
link_processor = None
research_engine = None
memory = None
bot_user_id = None

# Thread conversation history: { thread_ts: [{"role": ..., "content": ...}] }
_thread_history: dict[str, list[dict]] = defaultdict(list)
_thread_lock = threading.Lock()

MAX_THREAD_TURNS = 20


def set_dependencies(brain_inst, classifier_inst, link_proc_inst, research_inst, memory_inst):
    global brain, classifier, link_processor, research_engine, memory
    brain = brain_inst
    classifier = classifier_inst
    link_processor = link_proc_inst
    research_engine = research_inst
    memory = memory_inst


def _get_bot_user_id():
    global bot_user_id
    if bot_user_id is None:
        result = app.client.auth_test()
        bot_user_id = result["user_id"]
    return bot_user_id


def _add_to_thread(thread_ts: str, role: str, content: str):
    """Track conversation turns per Slack thread for multi-turn context."""
    with _thread_lock:
        history = _thread_history[thread_ts]
        history.append({"role": role, "content": content})
        if len(history) > MAX_THREAD_TURNS * 2:
            _thread_history[thread_ts] = history[-(MAX_THREAD_TURNS * 2):]


def _get_thread_history(thread_ts: str) -> list[dict]:
    with _thread_lock:
        return list(_thread_history.get(thread_ts, []))


def _run_in_background(fn, *args, **kwargs):
    """Run a function in a daemon thread so the Slack event loop isn't blocked."""
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


def _setup_handlers():
    """Register Slack event handlers on the app instance."""

    @app.event("message")
    def handle_message(event, say, logger):
        """Main message handler — classify and route."""
        if event.get("bot_id") or event.get("user") == _get_bot_user_id():
            return
        subtype = event.get("subtype")
        if subtype and subtype not in ("file_share",):
            return

        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event.get("ts")
        files = event.get("files", [])

        try:
            if files:
                for f in files:
                    mimetype = f.get("mimetype", "")
                    if mimetype.startswith("audio/"):
                        say(text="Voice note detected. Transcription coming in a future phase.", thread_ts=thread_ts)
                        return
                    if mimetype == "application/pdf":
                        say(text="PDF detected. Processing coming in a future phase.", thread_ts=thread_ts)
                        return

            if not text.strip():
                return

            # Check duplicate — but don't mark as seen yet
            if memory and memory.is_duplicate(text):
                logger.info("Duplicate message, skipping")
                return

            category = classifier.classify(text)
            logger.info(f"[{category}] {text[:80]}")

            # Track the user's message in thread history
            _add_to_thread(thread_ts, "user", text)

            # ── CHAT ─────────────────────────────────────────────────
            if category == "CHAT":
                if f"<@{_get_bot_user_id()}>" in text:
                    history = _get_thread_history(thread_ts)
                    response = brain.chat(text, thread_history=history[:-1] if len(history) > 1 else None)
                    say(text=response, thread_ts=thread_ts)
                    _add_to_thread(thread_ts, "assistant", response)
                # Mark as seen after handling
                if memory:
                    memory.mark_seen(text)
                return

            # ── URGENT ───────────────────────────────────────────────
            if category == "URGENT":
                response = brain.chat(
                    f"URGENT message from a team member: {text}\n\n"
                    "Respond with urgency. What should Batman do right now?"
                )
                say(text=f"*URGENT*\n{response}", thread_ts=thread_ts)
                _add_to_thread(thread_ts, "assistant", response)
                if memory:
                    memory.mark_seen(text)
                return

            # ── RESEARCH ─────────────────────────────────────────────
            if category == "RESEARCH":
                urls = re.findall(r"https?://[^\s<>]+", text)
                if urls:
                    def _process_links():
                        for url in urls[:3]:
                            say(text=f"Researching link: {url} ...", thread_ts=thread_ts)
                            summary = link_processor.process(url)
                            say(text=summary, thread_ts=thread_ts)
                            _add_to_thread(thread_ts, "assistant", summary)
                        if memory:
                            memory.mark_seen(text)

                    _run_in_background(_process_links)
                else:
                    say(text="Researching this for you, Batman...", thread_ts=thread_ts)

                    def _do_research():
                        try:
                            if Config.has_agent():
                                response = research_engine.deep_research(text)
                            else:
                                response = research_engine.quick_research(text)
                            say(text=response, thread_ts=thread_ts)
                            _add_to_thread(thread_ts, "assistant", response)
                        except Exception as e:
                            logger.error(f"Research failed: {e}", exc_info=True)
                            say(text="Research hit an error, Batman. I've logged it.", thread_ts=thread_ts)
                        if memory:
                            memory.mark_seen(text)

                    _run_in_background(_do_research)
                return

            # ── IDEA ─────────────────────────────────────────────────
            if category == "IDEA":
                say(text="Interesting idea. Let me score it...", thread_ts=thread_ts)
                score = brain.score_idea(text)
                say(text=score, thread_ts=thread_ts)
                _add_to_thread(thread_ts, "assistant", score)
                if memory:
                    memory.add_idea(text, score[:100])
                    memory.mark_seen(text)
                return

            # ── TASK ─────────────────────────────────────────────────
            if category == "TASK":
                response = brain.chat(
                    f"Task request: {text}\n\n"
                    "Acknowledge the task, clarify if needed, and ask for permission "
                    "before doing anything expensive."
                )
                say(text=response, thread_ts=thread_ts)
                _add_to_thread(thread_ts, "assistant", response)
                if memory:
                    memory.mark_seen(text)
                return

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            say(text="Something went wrong on my end, Batman. I've logged the error.", thread_ts=thread_ts)

    @app.event("app_mention")
    def handle_mention(event, say, logger):
        """Direct @ALFRED mentions always get a response."""
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event.get("ts")
        logger.info(f"Mentioned: {text[:80]}")

        _add_to_thread(thread_ts, "user", text)

        try:
            research_triggers = ["research", "look into", "find out", "what's happening with", "deep dive"]
            if any(trigger in text.lower() for trigger in research_triggers):
                say(text="On it, Batman. Running research...", thread_ts=thread_ts)

                def _do_mention_research():
                    try:
                        if Config.has_agent():
                            response = research_engine.deep_research(text)
                        else:
                            response = research_engine.quick_research(text)
                        say(text=response, thread_ts=thread_ts)
                        _add_to_thread(thread_ts, "assistant", response)
                    except Exception as e:
                        logger.error(f"Mention research failed: {e}", exc_info=True)
                        say(text="Research hit an error, Batman.", thread_ts=thread_ts)

                _run_in_background(_do_mention_research)
            else:
                history = _get_thread_history(thread_ts)
                response = brain.chat(text, thread_history=history[:-1] if len(history) > 1 else None)
                say(text=response, thread_ts=thread_ts)
                _add_to_thread(thread_ts, "assistant", response)
        except Exception as e:
            logger.error(f"Error handling mention: {e}", exc_info=True)
            say(text="Something went wrong, Batman.", thread_ts=thread_ts)


def start():
    """Initialize the Slack App and start Socket Mode. Called once from main."""
    global app
    app = App(token=Config.SLACK_BOT_TOKEN)
    _setup_handlers()
    handler = SocketModeHandler(app, Config.SLACK_APP_TOKEN)
    handler.start()
