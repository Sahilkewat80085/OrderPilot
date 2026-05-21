"""
Professional dual logging configuration for TradeForge.
Captures application events, request summaries, and tracebacks.
"""

import logging
from logging.handlers import RotatingFileHandler
from bot.config import settings


def setup_logging() -> logging.Logger:
    """
    Configures and returns the central logger.
    Directs standard messages to console, and full traces to a rotating file.
    """
    logger = logging.getLogger("tradeforge")
    logger.setLevel(logging.DEBUG)  # Capture all levels, filter via handlers
    
    # Avoid duplicating handlers if initialized multiple times
    if logger.hasHandlers():
        return logger

    # Ensure logs directory exists
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. File Handler: Captures deep debugging information with rotation
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s"
    )
    # Rotate at 5MB, keep up to 5 backups
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    # Log everything DEBUG and above to the file
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # 2. Console Handler: Clean, user-facing output
    console_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    # Console gets user-selected log level (default INFO)
    console_level = getattr(logging, settings.log_level, logging.INFO)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # Attach handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to the root logger to avoid double logging
    logger.propagate = False

    return logger


# Package-wide singleton logger
logger = setup_logging()
