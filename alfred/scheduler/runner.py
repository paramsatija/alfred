"""APScheduler setup — cron jobs for ALFRED."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from alfred.config import Config
from alfred.scheduler.jobs import (
    morning_briefing_job,
    reset_token_budget_job,
    health_check_job,
)

log = logging.getLogger("alfred.scheduler")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=Config.TIMEZONE)

    hour, minute = Config.WAKE_TIME.split(":")

    scheduler.add_job(
        morning_briefing_job,
        CronTrigger(hour=int(hour), minute=int(minute)),
        id="morning_briefing",
        name="Morning Briefing",
        replace_existing=True,
    )

    scheduler.add_job(
        reset_token_budget_job,
        CronTrigger(hour=0, minute=0),
        id="reset_tokens",
        name="Reset Token Budget",
        replace_existing=True,
    )

    scheduler.add_job(
        health_check_job,
        CronTrigger(minute="*/30"),
        id="health_check",
        name="Health Check",
        replace_existing=True,
    )

    scheduler.start()
    log.info(f"Scheduler started. Briefing at {Config.WAKE_TIME} {Config.TIMEZONE}")
    return scheduler
