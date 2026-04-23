"""ALFRED — AI Chief of Staff

Entry point. Starts the Slack bot, scheduler, and all subsystems.
"""

import os
import sys
import logging

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from alfred.config import Config
from alfred.utils.logging import setup_logging
from alfred.brain.client import Brain
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
    # Setup logging
    log = setup_logging()
    log.info("=" * 50)
    log.info("ALFRED — AI Chief of Staff — Starting Up")
    log.info("=" * 50)

    # Validate config
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
    research = ResearchEngine(brain, link_processor, memory)

    log.info("Initializing briefing generator...")
    briefing = BriefingGenerator(brain, research, memory)

    # Wire up dependencies
    slack_bot.set_dependencies(brain, classifier, link_processor)
    scheduler_jobs.set_dependencies(briefing, brain)

    # Start scheduler (background cron jobs)
    log.info("Starting scheduler...")
    scheduler = start_scheduler()

    # Post startup message to #alfred-logs
    try:
        post_log(
            "ALFRED is online.\n"
            f"Wake time: {Config.WAKE_TIME} {Config.TIMEZONE}\n"
            f"Daily token budget: {Config.DAILY_TOKEN_BUDGET:,} tokens\n"
            f"Research topics: {', '.join(memory.get_topics())}\n"
            "Ready to serve, sir."
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
        log.info("Goodbye, sir.")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        scheduler.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
