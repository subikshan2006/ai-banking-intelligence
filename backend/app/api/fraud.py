import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.fraud import FraudAlert
from app.models.transaction import Transaction
from app.schemas.fraud import FraudAnalysisRequest, FraudAnalysisResponse
from app.services.fraud_detection_service import fraud_service
from app.tools.fraud_tools import explain_flagged_transaction

router = APIRouter(prefix="/fraud", tags=["Fraud & Risk"])

@router.get("/alerts")
def list_fraud_alerts(
    risk_level: str | None = None,
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(FraudAlert)
    if risk_level:
        query = query.filter(FraudAlert.risk_level == risk_level.upper())
    if status:
        query = query.filter(FraudAlert.status == status.upper())

    total = query.count()
    alerts = query.order_by(FraudAlert.created_at.desc()).limit(limit).all()

    return {
        "total": total,
        "alerts": [
            {
                "id": a.id,
                "transaction_id": a.transaction_id,
                "customer_id": a.customer_id,
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "triggered_rules": json.loads(a.triggered_rules),
                "anomaly_score": a.anomaly_score,
                "is_ml_anomaly": bool(a.is_ml_anomaly),
                "evidence": json.loads(a.evidence),
                "recommended_action": a.recommended_action,
                "status": a.status,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]
    }

@router.post("/analyze", response_model=FraudAnalysisResponse)
def analyze_fraud_endpoint(request: FraudAnalysisRequest, db: Session = Depends(get_db)):
    if request.transaction_id:
        tx = db.query(Transaction).filter(Transaction.id == request.transaction_id.upper()).first()
        if not tx:
            raise HTTPException(status_code=404, detail=f"Transaction '{request.transaction_id}' not found.")
        return fraud_service.evaluate_transaction(db, tx)
    else:
        # Hypothetical transaction evaluation
        dummy_tx = Transaction(
            id="HYPO-001",
            account_id="ACC-DEMO",
            customer_id=request.customer_id or "CUST1001",
            amount=request.amount or 5000.0,
            txn_type="DEBIT",
            category="Shopping",
            merchant_name=request.merchant_name or "Online Store",
            location="Mumbai, IN",
            status="COMPLETED"
        )
        return fraud_service.evaluate_transaction(db, dummy_tx)

@router.get("/transaction/{transaction_id}")
def explain_transaction_risk(transaction_id: str, db: Session = Depends(get_db)):
    try:
        return explain_flagged_transaction(db, transaction_id=transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
