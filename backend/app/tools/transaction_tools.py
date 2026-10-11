from datetime import datetime, timedelta
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.models.transaction import Transaction

class AnalyzeCategoriesArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    period_days: int = Field(default=30, ge=1, le=180)

@registry.register(
    name="analyze_spending_categories",
    description="Analyze debit spending grouped by commercial category with ranking and proportions.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=AnalyzeCategoriesArgs
)
def analyze_spending_categories(db: Session, customer_id: str, period_days: int = 30) -> dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=period_days)
    txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id.upper(),
        Transaction.timestamp >= since,
        Transaction.txn_type == "DEBIT",
        Transaction.status == "COMPLETED"
    ).all()

    total_spend = sum(tx.amount for tx in txs)
    breakdown = {}
    for tx in txs:
        cat = tx.category or "Other"
        breakdown[cat] = breakdown.get(cat, 0.0) + tx.amount

    sorted_cats = [
        {
            "category": cat,
            "amount": round(amt, 2),
            "percentage": round((amt / max(1.0, total_spend)) * 100.0, 1)
        }
        for cat, amt in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "customer_id": customer_id.upper(),
        "period_days": period_days,
        "total_spend": round(total_spend, 2),
        "total_transactions": len(txs),
        "categories": sorted_cats
    }

class ComparePeriodsArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    current_days: int = Field(default=30, ge=1, le=90)
    prior_days: int = Field(default=30, ge=1, le=90)

@registry.register(
    name="compare_spending_periods",
    description="Compare spending trends between current period and preceding period to detect behavioral shifts.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=ComparePeriodsArgs
)
def compare_spending_periods(db: Session, customer_id: str, current_days: int = 30, prior_days: int = 30) -> dict[str, Any]:
    now = datetime.utcnow()
    current_start = now - timedelta(days=current_days)
    prior_start = current_start - timedelta(days=prior_days)

    curr_txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id.upper(),
        Transaction.timestamp >= current_start,
        Transaction.txn_type == "DEBIT",
        Transaction.status == "COMPLETED"
    ).all()

    prior_txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id.upper(),
        Transaction.timestamp >= prior_start,
        Transaction.timestamp < current_start,
        Transaction.txn_type == "DEBIT",
        Transaction.status == "COMPLETED"
    ).all()

    curr_total = sum(t.amount for t in curr_txs)
    prior_total = sum(t.amount for t in prior_txs)
    diff = curr_total - prior_total
    pct_change = round((diff / max(1.0, prior_total)) * 100.0, 1) if prior_total > 0 else 0.0

    return {
        "customer_id": customer_id.upper(),
        "current_period_days": current_days,
        "current_spending": round(curr_total, 2),
        "current_count": len(curr_txs),
        "prior_period_days": prior_days,
        "prior_spending": round(prior_total, 2),
        "prior_count": len(prior_txs),
        "absolute_change": round(diff, 2),
        "percentage_change": pct_change,
        "trend": "INCREASED" if diff > 0 else ("DECREASED" if diff < 0 else "STABLE")
    }

class CashFlowArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    period_days: int = Field(default=30, ge=1, le=180)

@registry.register(
    name="calculate_cash_flow",
    description="Calculate net liquidity and cash flow velocity (inflow vs outflow ratio).",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=CashFlowArgs
)
def calculate_cash_flow(db: Session, customer_id: str, period_days: int = 30) -> dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=period_days)
    txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id.upper(),
        Transaction.timestamp >= since,
        Transaction.status == "COMPLETED"
    ).all()

    inflow = sum(t.amount for t in txs if t.txn_type == "CREDIT")
    outflow = sum(t.amount for t in txs if t.txn_type == "DEBIT")
    savings_rate = round(((inflow - outflow) / max(1.0, inflow)) * 100.0, 1) if inflow > 0 else 0.0

    return {
        "customer_id": customer_id.upper(),
        "period_days": period_days,
        "total_inflow": round(inflow, 2),
        "total_outflow": round(outflow, 2),
        "net_cash_flow": round(inflow - outflow, 2),
        "savings_rate_percentage": savings_rate
    }
