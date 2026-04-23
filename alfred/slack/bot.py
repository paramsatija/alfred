"""Slack bot — event handlers for messages and mentions.

Routing logic:
  CHAT     → ignore (unless @ALFRED mentioned → quick chat)
  URGENT   → brain.chat with urgency framing → reply in thread
  RESEARCH → links: LinkProcessor | no links: ResearchEngine
  IDEA     → brain.score_idea → reply in thread
  TASK     → brain.chat with task framing → reply in thread
"""

import logging
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from alfred.config import Config

log = logging.getLogger("alfred.slack")

app = App(token=Config.SLACK_BOT_TOKEN)

# Dependencies injected by main.py
brain = None
classifier = None
link_processor = None
research_engine = None
memory = None
bot_user_id = None


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
        # Handle file uploads (voice/PDF stubs for future phases)
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

        # Skip duplicates
        if memory and memory.is_duplicate(text):
            logger.info("Duplicate message, skipping")
            return

        # Classify with Haiku (cheap)
        category = classifier.classify(text)
        logger.info(f"[{category}] {text[:80]}")

        # ── CHAT: ignore unless directly mentioned ───────────────────
        if category == "CHAT":
            if f"<@{_get_bot_user_id()}>" in text:
                response = brain.chat(text)
                say(text=response, thread_ts=thread_ts)
            return

        # ── URGENT: respond immediately with urgency ─────────────────
        if category == "URGENT":
            response = brain.chat(
                f"URGENT message from a team member: {text}\n\n"
                "Respond with urgency. What should Batman do right now?"
            )
            say(text=f"*URGENT*\n{response}", thread_ts=thread_ts)
            return

        # ── RESEARCH: links → LinkProcessor, no links → Research ─────
        if category == "RESEARCH":
            urls = re.findall(r"https?://[^\s<>]+", text)
            if urls:
                for url in urls[:3]:
                    say(text=f"Researching link: {url} ...", thread_ts=thread_ts)
                    summary = link_processor.process(url)
                    say(text=summary, thread_ts=thread_ts)
            else:
                # No URL — treat as a research question
                say(text="Researching this for you, Batman...", thread_ts=thread_ts)
                if Config.has_agent():
                    response = research_engine.deep_research(text)
                else:
                    response = research_engine.quick_research(text)
                say(text=response, thread_ts=thread_ts)
            return

        # ── IDEA: score it ───────────────────────────────────────────
        if category == "IDEA":
            say(text="Interesting idea. Let me score it...", thread_ts=thread_ts)
            score = brain.score_idea(text)
            say(text=score, thread_ts=thread_ts)
            if memory:
                memory.add_idea(text, score[:100])
            return

        # ── TASK: acknowledge and clarify ────────────────────────────
        if category == "TASK":
            response = brain.chat(
                f"Task request: {text}\n\n"
                "Acknowledge the task, clarify if needed, and ask for permission "
                "before doing anything expensive."
            )
            say(text=response, thread_ts=thread_ts)
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

    try:
        # Check if it's a research request
        research_triggers = ["research", "look into", "find out", "what's happening with", "deep dive"]
        if any(trigger in text.lower() for trigger in research_triggers):
            say(text="On it, Batman. Running research...", thread_ts=thread_ts)
            if Config.has_agent():
                response = research_engine.deep_research(text)
            else:
                response = research_engine.quick_research(text)
        else:
            response = brain.chat(text)

        say(text=response, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error handling mention: {e}", exc_info=True)
        say(text="Something went wrong, Batman.", thread_ts=thread_ts)


def start():
    handler = SocketModeHandler(app, Config.SLACK_APP_TOKEN)
    handler.start()
