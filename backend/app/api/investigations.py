import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.investigation import Investigation
from app.agents.supervisor import supervisor

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.get("")
def list_investigations(
    customer_id: str | None = None,
    risk_verdict: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Investigation)
    if customer_id:
        query = query.filter(Investigation.customer_id == customer_id.upper())
    if risk_verdict:
        query = query.filter(Investigation.risk_verdict == risk_verdict.upper())

    items = query.order_by(Investigation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": inv.id,
            "correlation_id": inv.correlation_id,
            "customer_id": inv.customer_id,
            "title": inv.title,
            "summary": inv.summary,
            "agents_involved": json.loads(inv.agents_involved),
            "risk_verdict": inv.risk_verdict,
            "status": inv.status,
            "created_at": inv.created_at.isoformat()
        }
        for inv in items
    ]

@router.get("/{investigation_id}")
def get_investigation_details(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id.upper()).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found.")
    
    return {
        "id": inv.id,
        "correlation_id": inv.correlation_id,
        "customer_id": inv.customer_id,
        "title": inv.title,
        "summary": inv.summary,
        "full_report": json.loads(inv.full_report),
        "agents_involved": json.loads(inv.agents_involved),
        "risk_verdict": inv.risk_verdict,
        "status": inv.status,
        "created_at": inv.created_at.isoformat()
    }

@router.post("")
async def create_investigation_endpoint(customer_id: str):
    """Manually initiate a full multi-agent 360 investigation workflow."""
    prompt = f"Generate a combined customer, risk, credit, and compliance report for {customer_id.upper()}."
    chat_resp = await supervisor.process_request(prompt)
    return {
        "correlation_id": chat_resp.correlation_id,
        "status": chat_resp.status,
        "answer": chat_resp.answer,
        "structured_data": chat_resp.structured_data,
        "agents_involved": chat_resp.agents_involved
    }
