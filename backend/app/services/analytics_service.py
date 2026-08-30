"""
Dashboard / analytics aggregation queries.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import RecoveryCase, RecoveryResult, AgentAction, RecoveryStatus


def get_overview(db: Session) -> dict:
    revenue_at_risk = db.query(func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0)).scalar()
    revenue_recovered = db.query(func.coalesce(func.sum(RecoveryResult.amount_recovered), 0)).scalar()

    failed_payments = db.query(func.count(RecoveryCase.id)).scalar()
    active_cases = db.query(func.count(RecoveryCase.id)).filter(
        RecoveryCase.status.in_([
            RecoveryStatus.OPEN, RecoveryStatus.ANALYZING, RecoveryStatus.ACTION_PENDING,
            RecoveryStatus.APPROVAL_REQUIRED, RecoveryStatus.IN_PROGRESS,
        ])
    ).scalar()

    agent_actions_count = db.query(func.count(AgentAction.id)).scalar()
    successful_actions = db.query(func.count(AgentAction.id)).filter(
        AgentAction.execution_status == "SUCCESS"
    ).scalar()

    avg_recovery_time = db.query(func.avg(RecoveryResult.recovery_time_seconds)).filter(
        RecoveryResult.status == "RECOVERED"
    ).scalar()

    recovery_rate = (revenue_recovered / revenue_at_risk * 100) if revenue_at_risk else 0.0
    agent_success_rate = (successful_actions / agent_actions_count * 100) if agent_actions_count else 0.0

    return {
        "revenue_at_risk": int(revenue_at_risk or 0),
        "revenue_recovered": int(revenue_recovered or 0),
        "recovery_rate": round(recovery_rate, 2),
        "failed_payments": int(failed_payments or 0),
        "abandoned_checkouts": 0,  # populate once checkout-abandonment events are wired up
        "active_recovery_cases": int(active_cases or 0),
        "agent_actions_count": int(agent_actions_count or 0),
        "agent_success_rate": round(agent_success_rate, 2),
        "average_recovery_time_seconds": float(avg_recovery_time) if avg_recovery_time else None,
    }
