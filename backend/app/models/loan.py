from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # LOAN3001
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), nullable=False, index=True)
    requested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), default="Personal")
    interest_rate: Mapped[float] = mapped_column(Float, default=10.5)  # annual percentage
    estimated_emi: Mapped[float] = mapped_column(Float, default=0.0)
    dti_ratio: Mapped[float] = mapped_column(Float, default=0.0)  # debt-to-income percentage (0-100)
    
    # Mathematical and rule-based evaluation outcome
    assessment_result: Mapped[str] = mapped_column(String(32), default="ELIGIBLE")  # ELIGIBLE, HIGH_RISK_DTI, REQUIRES_MANUAL_REVIEW, INELIGIBLE
    
    # Administrative / Committee simulated approval state
    approval_status: Mapped[str] = mapped_column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW, APPROVED, REJECTED
    
    assessment_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="loan_applications")
