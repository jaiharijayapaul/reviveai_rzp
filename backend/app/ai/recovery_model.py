"""
Thin re-export so `app.ai` exposes the prediction interface alongside the
agent and policy engine, per the original module layout.
"""
from app.services.prediction_service import prediction_service, FEATURE_ORDER  # noqa: F401
