from typing import Dict, Optional

import logging
from slack_sdk import WebClient
from alfred.config import Config

log = logging.getLogger("alfred.slack.senders")

client = WebClient(token=Config.SLACK_BOT_TOKEN)

# Channel name -> channel ID cache
_channel_cache: Dict[str, str] = {}


def _resolve_channel(name: str) -> Optional[str]:
    """Resolve channel name to ID."""
    if name in _channel_cache:
        return _channel_cache[name]

    clean_name = name.lstrip("#")
    try:
        result = client.conversations_list(types="public_channel", limit=200)
        for ch in result["channels"]:
            if ch["name"] == clean_name:
                _channel_cache[name] = ch["id"]
                return ch["id"]
    except Exception as e:
        log.error(f"Failed to resolve channel {name}: {e}")
    return None


def post_message(channel_name: str, text: str, thread_ts: Optional[str] = None):
    """Post a message to a channel by name."""
    channel_id = _resolve_channel(channel_name)
    if not channel_id:
        log.error(f"Channel not found: {channel_name}")
        return

    try:
        result = client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts,
            unfurl_links=False,
        )
        return result
    except Exception as e:
        log.error(f"Failed to post to {channel_name}: {e}")


def post_briefing(text: str):
    """Post morning briefing to #daily-briefing."""
    post_message("#daily-briefing", text)


def post_research(text: str):
    """Post research output to #research."""
    post_message("#research", text)


def post_idea(text: str):
    """Post scored idea to #ideas."""
    post_message("#ideas", text)


def post_log(text: str):
    """Post internal log to #alfred-logs."""
    post_message("#alfred-logs", text)


def dm_user(user_id: str, text: str):
    """Send a direct message to a user."""
    try:
        result = client.conversations_open(users=[user_id])
        dm_channel = result["channel"]["id"]
        client.chat_postMessage(channel=dm_channel, text=text)
    except Exception as e:
        log.error(f"Failed to DM user {user_id}: {e}")
