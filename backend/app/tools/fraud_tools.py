import json
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.models.transaction import Transaction
from app.models.fraud import FraudAlert
from app.services.fraud_detection_service import fraud_service

class AnalyzeTxArgs(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID to analyze, e.g. TXN4008")

@registry.register(
    name="analyze_transaction",
    description="Evaluate a specific transaction against fraud detection rules and experimental ML Isolation Forest.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=AnalyzeTxArgs
)
def analyze_transaction(db: Session, transaction_id: str) -> dict[str, Any]:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id.upper()).first()
    if not tx:
        raise ValueError(f"Transaction with ID '{transaction_id}' not found.")
    
    result = fraud_service.evaluate_transaction(db, tx)
    return result.model_dump()

class AnalyzeCustomerTxArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID, e.g. CUST1003")

@registry.register(
    name="analyze_customer_transactions",
    description="Analyze all recent transactions for a customer to detect suspicious spikes, bursts, or payment failures.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=AnalyzeCustomerTxArgs
)
def analyze_customer_transactions(db: Session, customer_id: str) -> dict[str, Any]:
    txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id.upper()
    ).order_by(Transaction.timestamp.desc()).limit(20).all()

    if not txs:
        return {
            "customer_id": customer_id.upper(),
            "analyzed_count": 0,
            "suspicious_count": 0,
            "overall_risk": "LOW",
            "findings": ["No transaction records found for customer."]
        }

    evaluations = [fraud_service.evaluate_transaction(db, tx).model_dump() for tx in txs]
    suspicious = [e for e in evaluations if e["risk_score"] >= 45]

    max_score = max((e["risk_score"] for e in evaluations), default=10)
    overall_risk = "HIGH" if max_score >= 75 else ("MEDIUM" if max_score >= 45 else "LOW")

    return {
        "customer_id": customer_id.upper(),
        "analyzed_count": len(txs),
        "suspicious_count": len(suspicious),
        "max_risk_score": max_score,
        "overall_risk": overall_risk,
        "flagged_transactions": suspicious,
        "summary": f"Analyzed {len(txs)} transactions: found {len(suspicious)} potentially suspicious items."
    }

class ExplainTxArgs(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID to explain, e.g. TXN4008")

@registry.register(
    name="explain_flagged_transaction",
    description="Provide human-readable explanation and rule breakdown for why a transaction was flagged.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=ExplainTxArgs
)
def explain_flagged_transaction(db: Session, transaction_id: str) -> dict[str, Any]:
    tx = db.query(Transaction).filter(Transaction.id == transaction_id.upper()).first()
    if not tx:
        raise ValueError(f"Transaction '{transaction_id}' not found.")
    
    # Check if existing alert exists
    alert = db.query(FraudAlert).filter(FraudAlert.transaction_id == tx.id).first()
    eval_resp = fraud_service.evaluate_transaction(db, tx)

    explanation = {
        "transaction_id": tx.id,
        "customer_id": tx.customer_id,
        "amount": tx.amount,
        "merchant": tx.merchant_name,
        "location": tx.location,
        "status": tx.status,
        "risk_score": eval_resp.risk_score,
        "risk_level": eval_resp.risk_level,
        "recommendation": eval_resp.recommendation,
        "rule_analysis": [
            {
                "rule": r.rule_name,
                "reason": r.description,
                "severity": r.severity
            }
            for r in eval_resp.rule_hits
        ],
        "ml_anomaly_analysis": {
            "model": eval_resp.ml_output.model_name,
            "raw_score": eval_resp.ml_output.raw_anomaly_score,
            "is_anomaly": eval_resp.ml_output.is_anomaly,
            "disclaimer": eval_resp.ml_output.disclaimer
        },
        "verdict_summary": f"Transaction {tx.id} for ₹{tx.amount:,.2f} at '{tx.merchant_name}' triggered {len(eval_resp.rule_hits)} policy rule(s). Recommended action: {eval_resp.recommendation}."
    }

    if alert:
        explanation["existing_alert_id"] = alert.id
        explanation["alert_status"] = alert.status

    return explanation

class GetAlertsArgs(BaseModel):
    customer_id: str | None = Field(default=None, description="Optional customer filter")

@registry.register(
    name="get_fraud_alerts",
    description="Retrieve open or investigated fraud alerts from the Fraud Center.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetAlertsArgs
)
def get_fraud_alerts(db: Session, customer_id: str | None = None) -> list[dict[str, Any]]:
    query = db.query(FraudAlert)
    if customer_id:
        query = query.filter(FraudAlert.customer_id == customer_id.upper())
    alerts = query.order_by(FraudAlert.created_at.desc()).limit(20).all()

    return [
        {
            "alert_id": a.id,
            "transaction_id": a.transaction_id,
            "customer_id": a.customer_id,
            "risk_score": a.risk_score,
            "risk_level": a.risk_level,
            "triggered_rules": json.loads(a.triggered_rules),
            "anomaly_score": a.anomaly_score,
            "is_ml_anomaly": bool(a.is_ml_anomaly),
            "recommended_action": a.recommended_action,
            "status": a.status,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]
