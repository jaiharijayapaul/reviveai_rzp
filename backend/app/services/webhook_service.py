"""
Webhook ingestion: signature verification + idempotent event storage.
"""
from sqlalchemy.orm import Session

from app.models import WebhookEvent
from app.utils.security import verify_razorpay_signature, payload_hash
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class WebhookVerificationError(Exception):
    pass


def process_webhook(db: Session, raw_body: bytes, signature: str, event_json: dict) -> WebhookEvent | None:
    """
    Verifies signature, deduplicates by event id / payload hash, and persists
    the event. Returns None if this event was already processed (duplicate).
    """
    settings = get_settings()
    if not verify_razorpay_signature(raw_body, signature, settings.RAZORPAY_WEBHOOK_SECRET):
        raise WebhookVerificationError("Invalid webhook signature")

    event_type = event_json.get("event", "unknown")
    # Razorpay payloads don't always carry a top-level unique event id in test
    # mode, so we fall back to the payload hash for idempotency.
    event_id = event_json.get("id") or payload_hash(raw_body)
    p_hash = payload_hash(raw_body)

    existing = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
    if existing:
        logger.info("Duplicate webhook event ignored: %s", event_id)
        return None

    event = WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        payload_hash=p_hash,
        processed=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
