import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration — all settings pulled from environment."""

    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Slack
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")

    # Managed Agent IDs (created by setup_agent.py)
    AGENT_ID = os.getenv("ALFRED_AGENT_ID", "")
    ENVIRONMENT_ID = os.getenv("ALFRED_ENVIRONMENT_ID", "")

    # Optional API keys for future phases
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")

    # Alfred behavior
    WAKE_TIME = os.getenv("ALFRED_WAKE_TIME", "10:00")
    TIMEZONE = os.getenv("ALFRED_TIMEZONE", "Asia/Kolkata")
    DAILY_TOKEN_BUDGET = int(os.getenv("ALFRED_DAILY_TOKEN_BUDGET", "500000"))
    LOG_LEVEL = os.getenv("ALFRED_LOG_LEVEL", "INFO")

    # Models — Haiku for cheap classification, Sonnet for balanced work
    MODEL_HAIKU = "claude-haiku-4-5-20251001"
    MODEL_SONNET = "claude-sonnet-4-6-20260414"

    # Managed Agent model (used for deep research, briefings, building)
    AGENT_MODEL = "claude-sonnet-4-6"

    # Slack channel names (resolved to IDs at runtime)
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
        """Check that all required env vars are set."""
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

    @classmethod
    def has_agent(cls):
        """Check if Managed Agent is configured."""
        return bool(cls.AGENT_ID and cls.ENVIRONMENT_ID)
