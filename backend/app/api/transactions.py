from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transaction import Transaction

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("")
def list_transactions(
    customer_id: str | None = None,
    category: str | None = None,
    status: str | None = None,
    is_flagged: bool | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    if customer_id:
        query = query.filter(Transaction.customer_id == customer_id.upper())
    if category:
        query = query.filter(Transaction.category.ilike(category))
    if status:
        query = query.filter(Transaction.status == status.upper())
    if is_flagged is not None:
        query = query.filter(Transaction.is_flagged == is_flagged)

    total = query.count()
    txs = query.order_by(Transaction.timestamp.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "transactions": [
            {
                "id": t.id,
                "account_id": t.account_id,
                "customer_id": t.customer_id,
                "amount": t.amount,
                "txn_type": t.txn_type,
                "category": t.category,
                "merchant_name": t.merchant_name,
                "location": t.location,
                "status": t.status,
                "timestamp": t.timestamp.isoformat(),
                "is_flagged": t.is_flagged,
                "description": t.description
            }
            for t in txs
        ]
    }

@router.get("/{transaction_id}")
def get_transaction_details(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id.upper()).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")

    return {
        "id": tx.id,
        "account_id": tx.account_id,
        "customer_id": tx.customer_id,
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
