"""
Unit tests for webhook signature verification and idempotency hashing.
"""
import hmac
import hashlib

from app.utils.security import verify_razorpay_signature, payload_hash


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_passes():
    secret = "test_webhook_secret"
    body = b'{"event": "payment.failed"}'
    sig = _sign(body, secret)
    assert verify_razorpay_signature(body, sig, secret) is True


def test_invalid_signature_fails():
    secret = "test_webhook_secret"
    body = b'{"event": "payment.failed"}'
    assert verify_razorpay_signature(body, "deadbeef", secret) is False


def test_tampered_payload_fails():
    secret = "test_webhook_secret"
    body = b'{"event": "payment.failed"}'
    sig = _sign(body, secret)
    tampered_body = b'{"event": "payment.captured"}'
    assert verify_razorpay_signature(tampered_body, sig, secret) is False


def test_missing_secret_or_signature_fails():
    assert verify_razorpay_signature(b"{}", "somesig", "") is False
    assert verify_razorpay_signature(b"{}", "", "somesecret") is False


def test_payload_hash_is_deterministic():
    body = b'{"a": 1}'
    assert payload_hash(body) == payload_hash(body)
    assert payload_hash(body) != payload_hash(b'{"a": 2}')
