# SPDX-License-Identifier: Apache-2.0
import logging
import os


def get_logger(name: str, level: str | int | None = None) -> logging.Logger:
    """Return a consistent application logger.

    Parameters
    ----------
    name: str
        Logger name, typically ``__name__``.
    level: str | int | None, optional
        Logging level (e.g. ``"INFO"``).  Defaults to the ``LOGLEVEL``
        environment variable or ``INFO``.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s %(name)s | %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    level_val = level if level is not None else os.getenv("LOGLEVEL", "INFO")
    if isinstance(level_val, int):
        logger.setLevel(level_val)
    else:
        logger.setLevel(level_val.upper())
    return logger

__all__ = ["get_logger"]
