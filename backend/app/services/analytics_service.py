"""
Dashboard / analytics aggregation queries.
"""
import datetime
from sqlalchemy import func, cast, Date
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

    fraud_prevented = db.query(func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0)).join(
        AgentAction, RecoveryCase.id == AgentAction.recovery_case_id
    ).filter(AgentAction.action_type == "FRAUD_LOCK").scalar()

    # Calculate recovery rate trend for the last 7 days
    end_date = datetime.datetime.utcnow().date()
    start_date = end_date - datetime.timedelta(days=6)
    
    # Query daily aggregates
    daily_stats = db.query(
        cast(RecoveryCase.created_at, Date).label("day"),
        func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0).label("at_risk"),
        func.coalesce(func.sum(RecoveryResult.amount_recovered), 0).label("recovered")
    ).outerjoin(
        RecoveryResult, RecoveryCase.id == RecoveryResult.recovery_case_id
    ).filter(
        cast(RecoveryCase.created_at, Date) >= start_date
    ).group_by(
        cast(RecoveryCase.created_at, Date)
    ).all()
    
    # Map results by date
    stats_map = {str(stat.day): stat for stat in daily_stats}
    
    recovery_rate_trend = []
    # Ensure all 7 days are in the list
    for i in range(7):
        current_date = start_date + datetime.timedelta(days=i)
        date_str = str(current_date)
        
        # Get day name like "Mon", "Tue"
        day_name = current_date.strftime("%a")
        
        stat = stats_map.get(date_str)
        if stat and stat.at_risk > 0:
            rate = float(stat.recovered) / float(stat.at_risk) * 100
        else:
            rate = 0.0
            
        recovery_rate_trend.append({
            "day": day_name,
            "rate": round(rate, 2)
        })

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
        "fraud_prevented": int(fraud_prevented or 0),
        "recovery_rate_trend": recovery_rate_trend,
    }
