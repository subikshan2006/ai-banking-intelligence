from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # POL-001
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # Lending, Fraud & AML, KYC & Compliance, Operations
    version: Mapped[str] = mapped_column(String(16), default="v1.0")
    effective_date: Mapped[str] = mapped_column(String(32), default="2026-01-01")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    passages: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of passage dicts: [{"id": "POL-001-P1", "text": "..."}]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
