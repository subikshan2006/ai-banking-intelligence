from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # ALERT5001
    transaction_id: Mapped[str] = mapped_column(String(32), ForeignKey("transactions.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"), nullable=False, index=True)
    
    # Transparent Rule-Based Score
    risk_score: Mapped[int] = mapped_column(Integer, default=0)  # 0 to 100
    risk_level: Mapped[str] = mapped_column(String(16), default="LOW")  # LOW, MEDIUM, HIGH
    triggered_rules: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of rule descriptions
    
    # Experimental ML Anomaly Output
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)  # IsolationForest raw decision function
    is_ml_anomaly: Mapped[bool] = mapped_column(Integer, default=0)
    
    evidence: Mapped[str] = mapped_column(Text, default="{}")  # JSON breakdown
    recommended_action: Mapped[str] = mapped_column(String(256), default="Review Recommended")
    ruleset_version: Mapped[str] = mapped_column(String(32), default="v2.4")
    model_version: Mapped[str] = mapped_column(String(32), default="IsolationForest-v1.0")
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN, UNDER_REVIEW, RESOLVED, FALSE_POSITIVE
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    transaction = relationship("Transaction", back_populates="fraud_alerts")
