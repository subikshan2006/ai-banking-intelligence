from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # ACC2001
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), default="SAVINGS")  # SAVINGS, CHECKING, FIXED_DEPOSIT
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE, FROZEN, DORMANT
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
