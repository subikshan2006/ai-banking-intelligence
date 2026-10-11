from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # INV6001
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    full_report: Mapped[str] = mapped_column(Text, nullable=False)  # JSON consolidated report
    agents_involved: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    risk_verdict: Mapped[str] = mapped_column(String(32), default="NORMAL")  # NORMAL, NEEDS_MONITORING, SUSPICIOUS_ACTIVITY
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
