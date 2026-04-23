import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Slack
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")

    # Brave Search
    BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")

    # OpenAI (Whisper)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Alpaca
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")

    # Alfred behavior
    WAKE_TIME = os.getenv("ALFRED_WAKE_TIME", "10:00")
    TIMEZONE = os.getenv("ALFRED_TIMEZONE", "Asia/Kolkata")
    DAILY_TOKEN_BUDGET = int(os.getenv("ALFRED_DAILY_TOKEN_BUDGET", "500000"))
    LOG_LEVEL = os.getenv("ALFRED_LOG_LEVEL", "INFO")

    # Model IDs
    MODEL_HAIKU = "claude-haiku-4-5-20251001"
    MODEL_SONNET = "claude-sonnet-4-6-20260414"
    MODEL_OPUS = "claude-opus-4-6-20260414"

    # Channel names (will be resolved to IDs on startup)
    CHANNELS = {
        "incoming": "#incoming",
        "briefing": "#daily-briefing",
        "research": "#research",
        "fertilizer": "#fertilizer-research",
        "ideas": "#ideas",
        "market": "#market-data",
        "builds": "#builds",
        "logs": "#alfred-logs",
    }

    # Data paths
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    CACHE_DIR = os.path.join(DATA_DIR, "cache")
    RESEARCH_DIR = os.path.join(DATA_DIR, "research")
    BUILDS_DIR = os.path.join(DATA_DIR, "builds")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if not cls.SLACK_BOT_TOKEN:
            missing.append("SLACK_BOT_TOKEN")
        if not cls.SLACK_SIGNING_SECRET:
            missing.append("SLACK_SIGNING_SECRET")
        if not cls.SLACK_APP_TOKEN:
            missing.append("SLACK_APP_TOKEN")
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
