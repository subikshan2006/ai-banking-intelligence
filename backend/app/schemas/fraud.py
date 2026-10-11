from typing import Any, Literal
from pydantic import BaseModel, Field

class RuleHit(BaseModel):
    rule_name: str
    condition: str
    threshold: Any
    observed_value: Any
    description: str
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"

class MLAnomalyOutput(BaseModel):
    model_name: str = "IsolationForest-v1.0"
    is_anomaly: bool = False
    raw_anomaly_score: float = 0.0  # Decision function output
    contamination_threshold: float = 0.05
    features_used: list[str] = Field(default_factory=lambda: ["normalized_amount", "hour_of_day", "day_of_week", "tx_frequency_1h"])
    disclaimer: str = "Experimental Anomaly Score: Uncalibrated heuristic — not conclusive proof of fraud."

class FraudAnalysisRequest(BaseModel):
    transaction_id: str | None = None
    customer_id: str | None = None
    amount: float | None = None
    merchant_name: str | None = None

class FraudAnalysisResponse(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    recommendation: Literal["Approve", "Review Recommended", "Block & Escalate"]
    rule_hits: list[RuleHit] = Field(default_factory=list)
    ml_output: MLAnomalyOutput
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    ruleset_version: str = "v2.4"
