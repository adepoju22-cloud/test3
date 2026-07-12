"""
Shared logging configuration for the entire application.

Every module obtains its logger via get_logger(__name__) so that log
records carry the originating module name while all of them share the
same handlers (console + rotating file at logs/scanner.log).
"""

import logging
from logging.handlers import RotatingFileHandler

from app.utils.config import get_settings

_CONFIGURED = False


def _configure_root_logger() -> None:
    """Attach console and rotating-file handlers to the root logger once."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        filename=str(settings.log_file),
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a module-level logger configured with shared handlers.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    _configure_root_logger()
    return logging.getLogger(name)
