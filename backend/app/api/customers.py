from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.tools.customer_tools import mask_account_number, summarize_transactions

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("")
def list_customers(
    search: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Customer)
    if search:
        s = f"%{search}%"
        query = query.filter((Customer.name.ilike(s)) | (Customer.id.ilike(s)) | (Customer.city.ilike(s)))
    
    total = query.count()
    customers = query.order_by(Customer.id.asc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone[:6] + "XXXX" if len(c.phone) > 6 else c.phone,
                "kyc_status": c.kyc_status,
                "risk_rating": c.risk_rating,
                "monthly_income": c.monthly_income,
                "employer": c.employer,
                "city": c.city,
                "created_at": c.created_at.isoformat()
            }
            for c in customers
        ]
    }

@router.get("/{customer_id}")
def get_customer_details(customer_id: str, db: Session = Depends(get_db)):
    cust = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    accounts = db.query(Account).filter(Account.customer_id == cust.id).all()
    recent_txs = db.query(Transaction).filter(
        Transaction.customer_id == cust.id
    ).order_by(Transaction.timestamp.desc()).limit(10).all()

    summary = summarize_transactions(db, cust.id, period_days=30)

    return {
        "customer": {
            "id": cust.id,
            "name": cust.name,
            "email": cust.email,
            "phone": cust.phone[:6] + "XXXX" if len(cust.phone) > 6 else cust.phone,
            "kyc_status": cust.kyc_status,
            "risk_rating": cust.risk_rating,
            "monthly_income": cust.monthly_income,
            "existing_monthly_debt": cust.existing_monthly_debt,
            "employer": cust.employer,
            "city": cust.city,
            "created_at": cust.created_at.isoformat()
        },
        "accounts": [
            {
                "id": a.id,
                "masked_account_number": mask_account_number(a.account_number),
                "account_type": a.account_type,
                "balance": a.balance,
                "currency": a.currency,
                "status": a.status
            }
            for a in accounts
        ],
        "recent_transactions": [
            {
                "id": t.id,
                "account_id": t.account_id,
                "amount": t.amount,
                "txn_type": t.txn_type,
                "category": t.category,
                "merchant_name": t.merchant_name,
                "status": t.status,
                "timestamp": t.timestamp.isoformat(),
                "is_flagged": t.is_flagged
            }
            for t in recent_txs
        ],
        "spending_summary": summary
    }

@router.get("/{customer_id}/accounts")
def get_customer_accounts_endpoint(customer_id: str, db: Session = Depends(get_db)):
    cust = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    
    accounts = db.query(Account).filter(Account.customer_id == cust.id).all()
    return [
        {
            "id": a.id,
            "customer_id": a.customer_id,
            "account_number": mask_account_number(a.account_number),
            "account_type": a.account_type,
            "balance": a.balance,
            "currency": a.currency,
            "status": a.status
        }
        for a in accounts
    ]

@router.get("/{customer_id}/transactions")
def get_customer_transactions_endpoint(
    customer_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    cust = db.query(Customer).filter(Customer.id == customer_id.upper()).first()
    if not cust:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")

    txs = db.query(Transaction).filter(
        Transaction.customer_id == cust.id
    ).order_by(Transaction.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": t.id,
            "account_id": t.account_id,
            "amount": t.amount,
            "txn_type": t.txn_type,
            "category": t.category,
            "merchant_name": t.merchant_name,
            "location": t.location,
            "status": t.status,
            "timestamp": t.timestamp.isoformat(),
            "is_flagged": t.is_flagged
        }
        for t in txs
    ]
