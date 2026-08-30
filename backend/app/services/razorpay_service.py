"""
Thin wrapper around the official `razorpay` Python SDK.

This is the ONLY module allowed to talk to Razorpay. The AI agent never
calls this directly — it goes through the policy engine and the
recovery_service first. All calls target Razorpay TEST MODE credentials.

Only operations that are actually documented in the Razorpay API are
implemented here. Nothing is invented.
"""
import requests
import razorpay
from razorpay.errors import BadRequestError, ServerError

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class RazorpayServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class RazorpayService:
    def __init__(self):
        settings = get_settings()
        self._settings = settings
        self._client = None
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self._client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

    @property
    def client(self) -> razorpay.Client:
        if self._client is None:
            raise RazorpayServiceError(
                "RAZORPAY_NOT_CONFIGURED",
                "Razorpay TEST MODE credentials are not configured.",
            )
        return self._client

    def create_order(self, amount: int, currency: str = "INR", receipt: str | None = None,
                      notes: dict | None = None) -> dict:
        """Orders API: POST /v1/orders"""
        try:
            return self.client.order.create({
                "amount": amount,
                "currency": currency,
                "receipt": receipt,
                "notes": notes or {},
            })
        except (BadRequestError, ServerError) as e:
            logger.error("razorpay create_order failed: %s", e)
            raise RazorpayServiceError("RAZORPAY_API_ERROR", "Unable to create order") from e

    def fetch_payment(self, payment_id: str) -> dict:
        """Payments API: GET /v1/payments/{id}"""
        try:
            return self.client.payment.fetch(payment_id)
        except (BadRequestError, ServerError) as e:
            logger.error("razorpay fetch_payment failed: %s", e)
            raise RazorpayServiceError("RAZORPAY_API_ERROR", "Unable to fetch payment") from e

    def create_payment_link(self, amount: int, description: str, currency: str = "INR",
                             customer: dict | None = None, notes: dict | None = None,
                             callback_url: str | None = None, options: dict | None = None) -> dict:
        """Payment Links API: POST /v1/payment_links — used to re-issue a fresh payment
        attempt for the customer when a direct retry isn't supported."""
        try:
            payload = {
                "amount": amount,
                "currency": currency,
                "description": description,
                "notes": notes or {},
            }
            if customer:
                payload["customer"] = customer
                payload["notify"] = {"sms": bool(customer.get("contact")), "email": bool(customer.get("email"))}
            if callback_url:
                payload["callback_url"] = callback_url
                payload["callback_method"] = "get"
            if options:
                payload["options"] = options
                
            return self.client.payment_link.create(payload)
        except (BadRequestError, ServerError) as e:
            logger.error("razorpay create_payment_link failed: %s", e)
            raise RazorpayServiceError("RAZORPAY_API_ERROR", "Unable to create payment link") from e

    def create_offer(self, name: str, discount_percent: int, max_discount: int = 100000, 
                     notes: dict | None = None) -> dict:
        """Offers API: POST /v1/offers - Used to create dynamic discounts"""
        try:
            payload = {
                "name": name,
                "active": True,
                "percent_rate": discount_percent,
                "max_discount_amount": max_discount,
                "min_amount": 100, # minimum 1 rupee
                "payment": {
                    "payment_methods": ["card", "netbanking", "wallet", "emi", "upi"]
                }
            }
            if notes:
                payload["notes"] = notes
                
            # Using requests directly as python sdk might not expose .offer directly
            auth = (self._settings.RAZORPAY_KEY_ID, self._settings.RAZORPAY_KEY_SECRET)
            res = requests.post("https://api.razorpay.com/v1/offers", json=payload, auth=auth)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            logger.error("razorpay create_offer failed: %s", e)
            raise RazorpayServiceError("RAZORPAY_API_ERROR", "Unable to create offer") from e


razorpay_service = RazorpayService()
