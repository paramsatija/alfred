"""Structured logging for ALFRED."""

import logging
import sys
from alfred.config import Config


def setup_logging():
    level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger("alfred")
    root.setLevel(level)
    root.addHandler(handler)

    # Quiet down noisy libraries
    for lib in ("httpx", "slack_bolt", "slack_sdk", "anthropic"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    return root
