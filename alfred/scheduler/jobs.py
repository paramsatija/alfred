"""Scheduled jobs — morning briefing, token reset, auto-research."""

from typing import Optional

import logging
from alfred.briefing.generator import BriefingGenerator
from alfred.brain.client import Brain
from alfred.slack.senders import post_log

log = logging.getLogger("alfred.scheduler")

# Will be set by main.py
briefing_generator: Optional[BriefingGenerator] = None
brain: Optional[Brain] = None


def set_dependencies(briefing: BriefingGenerator, brain_instance: Brain):
    global briefing_generator, brain
    briefing_generator = briefing
    brain = brain_instance


def morning_briefing_job():
    """Triggered at wake time — generates and posts morning briefing."""
    log.info("Morning briefing job triggered")
    try:
        briefing_generator.generate_and_post()
    except Exception as e:
        log.error(f"Morning briefing failed: {e}")
        post_log(f"Morning briefing failed: {e}")


def reset_token_budget_job():
    """Triggered at midnight — resets daily token budget."""
    log.info("Resetting daily token budget")
    if brain:
        brain.reset_daily_budget()
    post_log("Daily token budget reset. New day, new budget.")


def health_check_job():
    """Triggered every 30 min — posts heartbeat to logs."""
    log.info("Health check: ALFRED is alive")
