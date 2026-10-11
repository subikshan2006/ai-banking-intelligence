from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Explorer"])

@router.get("/logs")
def get_audit_logs(
    correlation_id: str | None = None,
    actor: str | None = None,
    event_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    events = audit_service.get_events(
        db=db,
        correlation_id=correlation_id,
        actor=actor,
        event_type=event_type,
        limit=limit,
        offset=offset
    )
    return {
        "count": len(events),
        "logs": [
            {
                "id": e.id,
                "correlation_id": e.correlation_id,
                "timestamp": e.timestamp.isoformat(),
                "actor": e.actor,
                "event_type": e.event_type,
                "tool_name": e.tool_name,
                "details": e.details,
                "duration_ms": e.duration_ms,
                "status": e.status
            }
            for e in events
        ]
    }
