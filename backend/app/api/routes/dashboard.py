from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import DashboardOverview
from app.services.analytics_service import get_overview

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview, summary="Top-line recovery metrics")
def overview(db: Session = Depends(get_db)):
    return get_overview(db)


@router.get("/revenue", summary="Revenue at risk vs recovered")
def revenue(db: Session = Depends(get_db)):
    data = get_overview(db)
    return {
        "revenue_at_risk": data["revenue_at_risk"],
        "revenue_recovered": data["revenue_recovered"],
    }


@router.get("/recovery-metrics", summary="Recovery rate + agent performance")
def recovery_metrics(db: Session = Depends(get_db)):
    data = get_overview(db)
    return {
        "recovery_rate": data["recovery_rate"],
        "agent_success_rate": data["agent_success_rate"],
        "average_recovery_time_seconds": data["average_recovery_time_seconds"],
    }


@router.get("/activity", summary="Recent agent activity feed")
def activity(db: Session = Depends(get_db), limit: int = 20):
    from app.models.models import AgentAction
    actions = db.query(AgentAction).order_by(AgentAction.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id, "recovery_case_id": a.recovery_case_id, "action_type": a.action_type,
            "confidence": float(a.confidence) if a.confidence is not None else None,
            "reasoning": a.reasoning, "policy_result": a.policy_result,
            "execution_status": a.execution_status, "created_at": a.created_at.isoformat(),
        }
        for a in actions
    ]
