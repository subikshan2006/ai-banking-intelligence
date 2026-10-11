from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.fraud import FraudAlert
from app.models.loan import LoanApplication
from app.models.approval import ApprovalRequest
from app.models.audit import AuditEvent
from app.services.simulation_service import simulation_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Calculate executive dashboard metrics live from authoritative database records."""
    total_customers = db.query(Customer).count()
    active_accounts = db.query(Account).filter(Account.status == "ACTIVE").count()
    
    # Financial aggregate metrics
    tx_stats = db.query(
        func.count(Transaction.id),
        func.sum(Transaction.amount)
    ).filter(Transaction.status == "COMPLETED").first()
    
    total_tx_count = tx_stats[0] or 0
    total_volume = float(tx_stats[1] or 0.0)

    # Fraud and Approvals counts
    open_alerts = db.query(FraudAlert).filter(FraudAlert.status == "OPEN").count()
    total_alerts = db.query(FraudAlert).count()
    pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").count()
    total_loans = db.query(LoanApplication).count()

    # Agent Activity counts from AuditEvent
    agent_executions = db.query(AuditEvent).filter(AuditEvent.actor.endswith("Agent")).count()

    # Recent Alerts
    recent_alerts_objs = db.query(FraudAlert).order_by(FraudAlert.created_at.desc()).limit(5).all()
    recent_alerts = [
        {
            "id": a.id,
            "transaction_id": a.transaction_id,
            "customer_id": a.customer_id,
            "risk_score": a.risk_score,
            "risk_level": a.risk_level,
            "status": a.status,
            "created_at": a.created_at.isoformat()
        }
        for a in recent_alerts_objs
    ]

    # Category Breakdown for Transactions
    cat_breakdown = db.query(
        Transaction.category,
        func.sum(Transaction.amount),
        func.count(Transaction.id)
    ).filter(Transaction.txn_type == "DEBIT").group_by(Transaction.category).all()

    category_spending = [
        {"category": cat, "amount": float(amt or 0), "count": cnt}
        for cat, amt, cnt in cat_breakdown
    ]

    # Risk Level distribution
    risk_dist = {
        "LOW": db.query(FraudAlert).filter(FraudAlert.risk_level == "LOW").count(),
        "MEDIUM": db.query(FraudAlert).filter(FraudAlert.risk_level == "MEDIUM").count(),
        "HIGH": db.query(FraudAlert).filter(FraudAlert.risk_level == "HIGH").count()
    }

    # Loan status distribution
    loan_dist = {
        "PENDING_REVIEW": db.query(LoanApplication).filter(LoanApplication.approval_status == "PENDING_REVIEW").count(),
        "APPROVED": db.query(LoanApplication).filter(LoanApplication.approval_status == "APPROVED").count(),
        "REJECTED": db.query(LoanApplication).filter(LoanApplication.approval_status == "REJECTED").count()
    }

    return {
        "metrics": {
            "total_customers": total_customers,
            "active_accounts": active_accounts,
            "total_transaction_volume": round(total_volume, 2),
            "total_transactions_count": total_tx_count,
            "open_fraud_alerts": open_alerts,
            "total_fraud_alerts": total_alerts,
            "pending_approvals": pending_approvals,
            "total_loans": total_loans,
            "agent_executions_count": agent_executions,
            "is_simulator_running": simulation_service.is_running
        },
        "recent_alerts": recent_alerts,
        "category_spending": category_spending,
        "risk_distribution": risk_dist,
        "loan_distribution": loan_dist
    }
