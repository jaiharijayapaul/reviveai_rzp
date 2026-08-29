"""
Structured logging setup. Never logs secrets, card numbers, or credentials.
"""
import logging
import sys

from app.config import get_settings

_SENSITIVE_KEYS = {"razorpay_key_secret", "razorpay_webhook_secret", "authorization", "card_number", "cvv"}


def redact(payload: dict) -> dict:
    """Shallow redaction of known-sensitive keys before logging."""
    return {
        k: ("***REDACTED***" if k.lower() in _SENSITIVE_KEYS else v)
        for k, v in payload.items()
    }


def get_logger(name: str) -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    return logger
