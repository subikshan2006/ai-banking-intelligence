from datetime import datetime, timedelta
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction

def mask_account_number(acc_num: str) -> str:
    if not acc_num or len(acc_num) < 4:
        return "****"
    return f"****-****-{acc_num[-4:]}"

class GetCustomerArgs(BaseModel):
    customer_id: str = Field(..., description="The unique customer identifier, e.g. CUST1001")

@registry.register(
    name="get_customer",
    description="Retrieve a customer's profile including KYC status, monthly income, and risk rating.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetCustomerArgs
)
def get_customer(db: Session, customer_id: str) -> dict[str, Any]:
    customer = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not customer:
        raise ValueError(f"Customer with ID '{customer_id}' not found.")
    return {
        "customer_id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone[:6] + "XXXX" if len(customer.phone) > 6 else customer.phone,
        "kyc_status": customer.kyc_status,
        "risk_rating": customer.risk_rating,
        "monthly_income": customer.monthly_income,
        "existing_monthly_debt": customer.existing_monthly_debt,
        "employer": customer.employer,
        "city": customer.city
    }

class GetAccountsArgs(BaseModel):
    customer_id: str = Field(..., description="The customer ID whose accounts should be retrieved")

@registry.register(
    name="get_customer_accounts",
    description="Retrieve all bank accounts associated with a customer with masked account numbers.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetAccountsArgs
)
def get_customer_accounts(db: Session, customer_id: str) -> list[dict[str, Any]]:
    accounts = db.query(Account).filter(Account.customer_id == customer_id.upper()).all()
    if not accounts:
        # Check if customer exists
        cust = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
        if not cust:
            raise ValueError(f"Customer with ID '{customer_id}' not found.")
        return []
    
    return [
        {
            "account_id": acc.id,
            "account_number": mask_account_number(acc.account_number),
            "account_type": acc.account_type,
            "balance": acc.balance,
            "currency": acc.currency,
            "status": acc.status
        }
        for acc in accounts
    ]

class GetBalanceArgs(BaseModel):
    account_id: str = Field(..., description="Account identifier, e.g. ACC2001")

@registry.register(
    name="get_account_balance",
    description="Retrieve the current ledger balance and status of a specific bank account.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetBalanceArgs
)
def get_account_balance(db: Session, account_id: str) -> dict[str, Any]:
    account = db.query(Account).filter(Account.id == account_id.upper()).first()
    if not account:
        raise ValueError(f"Account with ID '{account_id}' not found.")
    return {
        "account_id": account.id,
        "customer_id": account.customer_id,
        "masked_account_number": mask_account_number(account.account_number),
        "balance": account.balance,
        "currency": account.currency,
        "status": account.status
    }

class GetTransactionsArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    limit: int = Field(default=10, ge=1, le=100)
    category: str | None = Field(default=None, description="Optional category filter")

@registry.register(
    name="get_transactions",
    description="Retrieve recent transactions for a customer, optionally filtered by category.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=GetTransactionsArgs
)
def get_transactions(db: Session, customer_id: str, limit: int = 10, category: str | None = None) -> list[dict[str, Any]]:
    query = db.query(Transaction).filter(Transaction.customer_id == customer_id.upper())
    if category:
        query = query.filter(Transaction.category.ilike(category))
    txs = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "transaction_id": tx.id,
            "account_id": tx.account_id,
            "amount": tx.amount,
            "txn_type": tx.txn_type,
            "category": tx.category,
            "merchant_name": tx.merchant_name,
            "location": tx.location,
            "status": tx.status,
            "timestamp": tx.timestamp.isoformat(),
            "is_flagged": tx.is_flagged,
            "description": tx.description
        }
        for tx in txs
    ]

class SummarizeTransactionsArgs(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    period_days: int = Field(default=30, ge=1, le=365)

@registry.register(
    name="summarize_transactions",
    description="Calculate income, total expenditures, net cash flow, and category breakdown for a customer.",
    permission="READ_ONLY",
    is_state_changing=False,
    args_schema=SummarizeTransactionsArgs
)
def summarize_transactions(db: Session, customer_id: str, period_days: int = 30) -> dict[str, Any]:
    since = datetime.utcnow() - timedelta(days=period_days)
    txs = db.query(Transaction).filter(
        Transaction.customer_id == customer_id.upper(),
        Transaction.timestamp >= since,
        Transaction.status == "COMPLETED"
    ).all()

    inflow = sum(tx.amount for tx in txs if tx.txn_type == "CREDIT")
    outflow = sum(tx.amount for tx in txs if tx.txn_type == "DEBIT")
    
    cat_totals: dict[str, dict[str, Any]] = {}
    for tx in txs:
        if tx.txn_type == "DEBIT":
            if tx.category not in cat_totals:
                cat_totals[tx.category] = {"total": 0.0, "count": 0}
            cat_totals[tx.category]["total"] += tx.amount
            cat_totals[tx.category]["count"] += 1

    categories = [
        {
            "category": cat,
            "total_amount": round(info["total"], 2),
            "transaction_count": info["count"],
            "percentage": round((info["total"] / max(1.0, outflow)) * 100.0, 1)
        }
        for cat, info in sorted(cat_totals.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    return {
        "customer_id": customer_id.upper(),
        "period_days": period_days,
        "transaction_count": len(txs),
        "total_inflow": round(inflow, 2),
        "total_outflow": round(outflow, 2),
        "net_cashflow": round(inflow - outflow, 2),
        "categories": categories
    }
