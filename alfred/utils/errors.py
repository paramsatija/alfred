"""Error handling utilities."""

import logging
import functools
import traceback

log = logging.getLogger("alfred.errors")


def safe_handler(func):
    """Decorator to catch and log errors without crashing the bot."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in {func.__name__}: {e}\n{traceback.format_exc()}")
            return None
    return wrapper


def safe_async_handler(func):
    """Async version of safe_handler."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in {func.__name__}: {e}\n{traceback.format_exc()}")
            return None
    return wrapper
