from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.db import get_db
from backend.database.models import QueryLog, User
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/eval")


@router.get("/logs")
def get_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = (
        db.query(QueryLog)
        .filter(QueryLog.user_id == current_user.id)
        .order_by(QueryLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": l.id, "question": l.question, "num_sources": l.num_sources,
            "confidence": l.confidence, "verified": l.verified,
            "latency_ms": round(l.latency_ms, 1) if l.latency_ms else None,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(QueryLog).filter(QueryLog.user_id == current_user.id)
    total = q.count()
    if total == 0:
        return {"total_queries": 0}

    avg_latency = db.query(func.avg(QueryLog.latency_ms)).filter(QueryLog.user_id == current_user.id).scalar()
    unverified = q.filter(QueryLog.verified == False).count()  # noqa: E712
    by_confidence = {}
    for conf in ["high", "medium", "low"]:
        by_confidence[conf] = q.filter(QueryLog.confidence == conf).count()

    return {
        "total_queries": total,
        "avg_latency_ms": round(avg_latency, 1) if avg_latency else None,
        "unverified_count": unverified,
        "confidence_breakdown": by_confidence,
    }
