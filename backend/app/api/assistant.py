from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.supervisor import supervisor
from app.services.audit_service import audit_service

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Entry point for natural-language multi-agent banking interactions."""
    try:
        response = await supervisor.process_request(
            message=request.message,
            correlation_id=request.correlation_id,
            demo_role=request.demo_role
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant orchestration error: {str(e)}")

@router.get("/traces/{correlation_id}")
def get_trace_events(correlation_id: str, db: Session = Depends(get_db)):
    """Retrieve all chronological audit events and tool traces for a specific correlation ID."""
    events = audit_service.get_events(db=db, correlation_id=correlation_id, limit=50)
    if not events:
        raise HTTPException(status_code=404, detail=f"No trace records found for correlation ID '{correlation_id}'.")
    return [
        {
            "id": e.id,
            "correlation_id": e.correlation_id,
            "timestamp": e.timestamp.isoformat(),
            "actor": e.actor,
            "event_type": e.event_type,
            "tool_name": e.tool_name,
            "duration_ms": e.duration_ms,
            "status": e.status,
            "details": e.details
        }
        for e in events
    ]
