"""ALFRED — AI Chief of Staff

Entry point. Validates config, initializes subsystems, starts Slack bot.

Architecture:
  - Regular API calls (Haiku/Sonnet) for classification, chat, scoring
  - Managed Agent sessions for deep research, morning briefings
  - Native web_search replaces Brave Search
  - APScheduler for cron jobs (briefing, token reset, health check)
  - Slack Socket Mode for real-time message handling
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from alfred.config import Config
from alfred.utils.logging import setup_logging
from alfred.brain.api import Brain
from alfred.intelligence.classifier import Classifier
from alfred.intelligence.link_processor import LinkProcessor
from alfred.memory.store import MemoryStore
from alfred.research.engine import ResearchEngine
from alfred.briefing.generator import BriefingGenerator
from alfred.scheduler import jobs as scheduler_jobs
from alfred.scheduler.runner import start_scheduler
from alfred.slack import bot as slack_bot
from alfred.slack.senders import post_log


def main():
    log = setup_logging()
    log.info("=" * 50)
    log.info("ALFRED — AI Chief of Staff — Starting Up")
    log.info("=" * 50)

    # Validate required config
    try:
        Config.validate()
    except ValueError as e:
        log.error(f"Configuration error: {e}")
        log.error("Copy .env.example to .env and fill in your API keys")
        sys.exit(1)

    # Ensure data directories exist
    for d in [Config.DATA_DIR, Config.CACHE_DIR, Config.RESEARCH_DIR, Config.BUILDS_DIR]:
        os.makedirs(d, exist_ok=True)

    # Initialize components
    log.info("Initializing brain (Claude API)...")
    brain = Brain()

    log.info("Initializing memory store...")
    memory = MemoryStore()

    log.info("Initializing intelligence layer...")
    classifier = Classifier(brain)
    link_processor = LinkProcessor(brain)

    log.info("Initializing research engine...")
    research = ResearchEngine(brain, memory)

    log.info("Initializing briefing generator...")
    briefing = BriefingGenerator(brain, memory)

    # Check Managed Agent status
    if Config.has_agent():
        log.info(f"Managed Agent configured: {Config.AGENT_ID[:20]}...")
        log.info("Deep research and briefings will use autonomous agent sessions")
    else:
        log.warning(
            "Managed Agent NOT configured. "
            "Run 'python -m alfred.setup_agent' for full capabilities. "
            "Falling back to regular API calls with web_search tool."
        )

    # Wire dependencies into Slack bot and scheduler
    slack_bot.set_dependencies(brain, classifier, link_processor, research, memory)
    scheduler_jobs.set_dependencies(briefing)

    # Start scheduler
    log.info("Starting scheduler...")
    scheduler = start_scheduler()

    # Post startup message
    try:
        agent_status = "Managed Agent active" if Config.has_agent() else "API-only mode (no Managed Agent)"
        post_log(
            "ALFRED is online.\n"
            f"Mode: {agent_status}\n"
            f"Wake time: {Config.WAKE_TIME} {Config.TIMEZONE}\n"
            f"Daily token budget: {Config.DAILY_TOKEN_BUDGET:,} tokens\n"
            f"Research topics: {', '.join(memory.get_topics())}\n"
            "Ready to serve, Batman."
        )
    except Exception as e:
        log.warning(f"Could not post startup message to Slack: {e}")

    # Start Slack bot (blocks — this is the main loop)
    log.info("Starting Slack bot (Socket Mode)...")
    log.info("ALFRED is ready. Listening for messages...")
    try:
        slack_bot.start()
    except KeyboardInterrupt:
        log.info("Shutting down ALFRED...")
        scheduler.shutdown()
        log.info("Goodbye, Batman.")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        scheduler.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
