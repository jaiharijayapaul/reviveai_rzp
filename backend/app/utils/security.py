"""
Security utilities: Razorpay webhook signature verification, idempotency helpers.
"""
import hashlib
import hmac


def verify_razorpay_signature(payload_body: bytes, signature: str, webhook_secret: str) -> bool:
    """
    Verify Razorpay webhook signature per Razorpay's documented HMAC-SHA256 scheme:
    signature = HMAC_SHA256(payload_body, webhook_secret), hex-encoded.
    """
    if not webhook_secret or not signature:
        return False
    expected = hmac.new(
        key=webhook_secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def payload_hash(payload_body: bytes) -> str:
    """Deterministic hash of a webhook payload, used for dedup / audit trail."""
    return hashlib.sha256(payload_body).hexdigest()
