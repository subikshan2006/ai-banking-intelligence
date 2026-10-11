from datetime import datetime, timedelta
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

def default_expiry():
    return datetime.utcnow() + timedelta(hours=24)

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # APPR7001
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)  # FREEZE_ACCOUNT, HIGH_VALUE_TRANSFER, OVERRIDE_LOAN, POLICY_EXCEPTION
    
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON serialized dictionary
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 of canonical JSON
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    
    risk_level: Mapped[str] = mapped_column(String(16), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED, EXPIRED
    
    decision_by: Mapped[str] = mapped_column(String(64), nullable=True)  # Demo role or username e.g. "compliance_manager"
    decision_reason: Mapped[str] = mapped_column(Text, nullable=True)
    decision_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    execution_result: Mapped[str] = mapped_column(Text, nullable=True)  # JSON output of simulated action
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=default_expiry)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
