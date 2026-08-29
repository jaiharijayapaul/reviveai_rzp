"""
Sanity tests for the prediction service's heuristic fallback (works even
without a trained model artifact present).
"""
from app.services.prediction_service import PredictionService


def test_heuristic_outputs_are_bounded():
    svc = PredictionService()
    features = {
        "amount": 99900, "previous_attempts": 1, "previous_successful_payments": 4,
        "previous_failed_payments": 0, "checkout_abandonment_minutes": 2,
        "hour_of_day": 14, "is_temporary_failure": 1,
    }
    result = svc.predict(features)
    assert 0.0 <= result["recovery_probability"] <= 1.0
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_high_amount_is_flagged_high_risk():
    svc = PredictionService()
    features = {"amount": 8_000_000, "previous_attempts": 1}
    result = svc.predict(features)
    assert result["risk_level"] == "HIGH"


def test_good_customer_history_increases_probability():
    svc = PredictionService()
    good = svc.predict({"amount": 99900, "previous_successful_payments": 10, "previous_failed_payments": 0, "is_temporary_failure": 1})
    bad = svc.predict({"amount": 99900, "previous_successful_payments": 0, "previous_failed_payments": 8, "is_temporary_failure": 0})
    assert good["recovery_probability"] > bad["recovery_probability"]
