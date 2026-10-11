from datetime import datetime
from sqlalchemy import String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # CUST1001
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    kyc_status: Mapped[str] = mapped_column(String(32), default="VERIFIED")  # VERIFIED, PENDING, REJECTED
    risk_rating: Mapped[str] = mapped_column(String(32), default="LOW")  # LOW, MEDIUM, HIGH
    monthly_income: Mapped[float] = mapped_column(Float, default=0.0)
    existing_monthly_debt: Mapped[float] = mapped_column(Float, default=0.0)
    employer: Mapped[str] = mapped_column(String(128), default="Enterprise Corp")
    city: Mapped[str] = mapped_column(String(64), default="Mumbai")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    loan_applications = relationship("LoanApplication", back_populates="customer", cascade="all, delete-orphan")
