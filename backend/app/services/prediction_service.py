"""
Wraps the trained ML model to produce a recovery_probability + risk level
for a given transaction context. Falls back to a transparent heuristic if
no trained model artifact is present (so the app never crashes / always demos).
"""
from pathlib import Path
import joblib
import numpy as np

from app.utils.logging import get_logger

logger = get_logger(__name__)

MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "recovery_model.joblib"

FEATURE_ORDER = [
    "amount",                      # transaction amount (paise)
    "previous_attempts",           # attempts on this order so far
    "previous_successful_payments",  # customer's historical successful payments
    "previous_failed_payments",    # customer's historical failed payments
    "checkout_abandonment_minutes",  # minutes since last activity (0 if not abandonment)
    "hour_of_day",                 # 0-23
    "is_temporary_failure",        # 1 if failure reason looks transient (timeout/network)
]


class PredictionService:
    def __init__(self):
        self._model = None
        self._load()

    def _load(self):
        if MODEL_PATH.exists():
            try:
                self._model = joblib.load(MODEL_PATH)
                logger.info("Loaded recovery model from %s", MODEL_PATH)
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to load model artifact, falling back to heuristic: %s", e)
                self._model = None
        else:
            logger.warning("No trained model artifact found at %s — using heuristic fallback.", MODEL_PATH)

    def predict(self, features: dict) -> dict:
        """
        features: dict matching FEATURE_ORDER keys (missing keys default sensibly).
        Returns: {"recovery_probability": float, "risk_level": "LOW"|"MEDIUM"|"HIGH"}
        """
        vector = self._vectorize(features)

        if self._model is not None:
            try:
                proba = float(self._model.predict_proba([vector])[0][1])
            except Exception as e:  # noqa: BLE001
                logger.warning("Model inference failed, using heuristic: %s", e)
                proba = self._heuristic(features)
        else:
            proba = self._heuristic(features)

        proba = max(0.0, min(1.0, proba))
        return {
            "recovery_probability": round(proba, 3),
            "risk_level": self._risk_level(proba, features),
        }

    @staticmethod
    def _vectorize(f: dict) -> list[float]:
        return [
            float(f.get("amount", 0)),
            float(f.get("previous_attempts", 1)),
            float(f.get("previous_successful_payments", 0)),
            float(f.get("previous_failed_payments", 0)),
            float(f.get("checkout_abandonment_minutes", 0)),
            float(f.get("hour_of_day", 12)),
            float(f.get("is_temporary_failure", 0)),
        ]

    @staticmethod
    def _heuristic(f: dict) -> float:
        """Transparent, explainable fallback used if no model is trained yet."""
        score = 0.5
        score += 0.05 * min(f.get("previous_successful_payments", 0), 6)
        score -= 0.08 * min(f.get("previous_failed_payments", 0), 5)
        score -= 0.05 * max(f.get("previous_attempts", 1) - 1, 0)
        if f.get("is_temporary_failure"):
            score += 0.2
        if 0 < f.get("checkout_abandonment_minutes", 0) <= 5:
            score += 0.1
        if f.get("amount", 0) > 5_000_000:  # > ₹50,000
            score -= 0.15
        return score

    @staticmethod
    def _risk_level(proba: float, f: dict) -> str:
        if f.get("amount", 0) > 5_000_000 or proba < 0.35:
            return "HIGH"
        if proba < 0.65:
            return "MEDIUM"
        return "LOW"


prediction_service = PredictionService()
