from datetime import datetime
from sqlalchemy import String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # TXN4001
    account_id: Mapped[str] = mapped_column(String(32), ForeignKey("accounts.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    txn_type: Mapped[str] = mapped_column(String(16), nullable=False)  # CREDIT, DEBIT
    category: Mapped[str] = mapped_column(String(32), default="General")  # Salary, Groceries, Shopping, Utility, Transfer, Travel, Dining
    merchant_name: Mapped[str] = mapped_column(String(128), default="Store")
    location: Mapped[str] = mapped_column(String(64), default="Mumbai, IN")
    status: Mapped[str] = mapped_column(String(16), default="COMPLETED")  # COMPLETED, FAILED
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    description: Mapped[str] = mapped_column(String(256), default="")

    account = relationship("Account", back_populates="transactions")
    fraud_alerts = relationship("FraudAlert", back_populates="transaction", cascade="all, delete-orphan")
