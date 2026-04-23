import logging
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from alfred.config import Config

log = logging.getLogger("alfred.slack")

app = App(token=Config.SLACK_BOT_TOKEN)

# Will be set by main.py
brain = None
classifier = None
link_processor = None
bot_user_id = None


def set_dependencies(brain_instance, classifier_instance, link_processor_instance):
    global brain, classifier, link_processor
    brain = brain_instance
    classifier = classifier_instance
    link_processor = link_processor_instance


def _get_bot_user_id():
    global bot_user_id
    if bot_user_id is None:
        result = app.client.auth_test()
        bot_user_id = result["user_id"]
    return bot_user_id


@app.event("message")
def handle_message(event, say, logger):
    if event.get("bot_id") or event.get("user") == _get_bot_user_id():
        return
    subtype = event.get("subtype")
    if subtype and subtype not in ("file_share",):
        return

    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    files = event.get("files", [])

    logger.info(f"Message: {text[:100]}")

    try:
        # File uploads
        if files:
            for f in files:
                mimetype = f.get("mimetype", "")
                if mimetype.startswith("audio/"):
                    say(text="Voice note detected. Transcription coming in Phase 2.", thread_ts=thread_ts)
                    return
                if mimetype == "application/pdf":
                    say(text="PDF detected. Processing coming in Phase 2.", thread_ts=thread_ts)
                    return

        if not text.strip():
            return

        # Classify
        category = classifier.classify(text)
        logger.info(f"Classified as: {category}")

        if category == "CHAT":
            if f"<@{_get_bot_user_id()}>" in text:
                response = brain.chat(text)
                say(text=response, thread_ts=thread_ts)
            return

        if category == "URGENT":
            response = brain.chat(f"URGENT message from a team member: {text}\n\nRespond with urgency. What should sir do?")
            say(text=f"*URGENT*\n{response}", thread_ts=thread_ts)
            return

        if category == "RESEARCH":
            urls = re.findall(r'https?://[^\s<>]+', text)
            if urls:
                for url in urls[:3]:
                    say(text=f"Researching link: {url} ...", thread_ts=thread_ts)
                    summary = link_processor.process(url)
                    say(text=summary, thread_ts=thread_ts)
            else:
                response = brain.chat(f"Research request: {text}\n\nProvide initial thoughts and offer to do deep research.")
                say(text=response, thread_ts=thread_ts)
            return

        if category == "IDEA":
            say(text="Interesting idea. Let me score it...", thread_ts=thread_ts)
            score = brain.score_idea(text)
            say(text=score, thread_ts=thread_ts)
            return

        if category == "TASK":
            response = brain.chat(f"Task request: {text}\n\nAcknowledge the task, clarify if needed, and ask for permission before doing anything expensive.")
            say(text=response, thread_ts=thread_ts)
            return

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        say(text="Something went wrong on my end, sir. I've logged the error.", thread_ts=thread_ts)


@app.event("app_mention")
def handle_mention(event, say, logger):
    text = event.get("text", "")
    thread_ts = event.get("thread_ts") or event.get("ts")
    logger.info(f"Mentioned: {text[:100]}")
    try:
        response = brain.chat(text)
        say(text=response, thread_ts=thread_ts)
    except Exception as e:
        logger.error(f"Error handling mention: {e}", exc_info=True)
        say(text="Something went wrong, sir.", thread_ts=thread_ts)


def start():
    log.info("Starting ALFRED Slack bot...")
    handler = SocketModeHandler(app, Config.SLACK_APP_TOKEN)
    handler.start()
