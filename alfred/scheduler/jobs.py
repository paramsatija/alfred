"""Scheduled jobs — morning briefing, token reset, health check."""

import logging
from alfred.briefing.generator import BriefingGenerator
from alfred.brain.api import Brain
from alfred.slack.senders import post_log

log = logging.getLogger("alfred.scheduler")

briefing_generator: BriefingGenerator | None = None
brain: Brain | None = None


def set_dependencies(briefing: BriefingGenerator, brain_instance: Brain):
    global briefing_generator, brain
    briefing_generator = briefing
    brain = brain_instance


def morning_briefing_job():
    log.info("Morning briefing job triggered")
    try:
        briefing_generator.generate_and_post()
    except Exception as e:
        log.error(f"Morning briefing failed: {e}")
        post_log(f"Morning briefing failed: {e}")


def reset_token_budget_job():
    log.info("Resetting daily token budget")
    if brain:
        brain.reset_daily_budget()
    post_log("Daily token budget reset. New day, Batman.")


def health_check_job():
    log.info("Health check: ALFRED is alive")
