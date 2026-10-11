from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SupervisorAgent, FraudAgent, User, etc.
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # TOOL_INVOKED, APPROVAL_DECIDED, etc.
    tool_name: Mapped[str] = mapped_column(String(64), default="", index=True)
    details: Mapped[str] = mapped_column(Text, default="{}")  # JSON metadata (PII masked)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS")  # SUCCESS, ERROR, REJECTED, INFO
