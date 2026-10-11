import os
import json
import logging
from datetime import datetime, timedelta
import numpy as np
import joblib
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.fraud import FraudAlert
from app.schemas.fraud import RuleHit, MLAnomalyOutput, FraudAnalysisResponse

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "isolation_forest.joblib")

class FraudDetectionService:
    def __init__(self):
        self._ml_model = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self._ml_model = joblib.load(MODEL_PATH)
            except Exception as e:
                logger.warning(f"Could not load IsolationForest model: {e}")

    def evaluate_transaction(self, db: Session, transaction: Transaction) -> FraudAnalysisResponse:
        rule_hits: list[RuleHit] = []
        evidence: dict = {}
        
        # 1. Historical Baseline Analysis
        past_txs = db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.id != transaction.id,
            Transaction.status == "COMPLETED"
        ).all()

        if past_txs:
            amounts = [t.amount for t in past_txs]
            median_amt = float(np.median(amounts))
            mean_amt = float(np.mean(amounts))
            std_amt = float(np.std(amounts)) if len(amounts) > 1 else 0.0

            evidence["historical_tx_count"] = len(past_txs)
            evidence["historical_median_amount"] = round(median_amt, 2)
            evidence["historical_mean_amount"] = round(mean_amt, 2)

            # Rule: High Amount relative to history (> 3x median and > mean + 2*std)
            threshold = max(50000.0, median_amt * 3.0)
            if transaction.amount >= threshold:
                rule_hits.append(RuleHit(
                    rule_name="HIGH_AMOUNT_VS_HISTORICAL_BASELINE",
                    condition="Transaction amount exceeds 3x customer median amount and 50,000 threshold",
                    threshold=round(threshold, 2),
                    observed_value=round(transaction.amount, 2),
                    description=f"Transaction ₹{transaction.amount:,.2f} is {round(transaction.amount / max(1.0, median_amt), 1)}x higher than typical spending.",
                    severity="HIGH" if transaction.amount > 200000.0 else "MEDIUM"
                ))
        else:
            evidence["historical_tx_count"] = 0
            evidence["note"] = "New account with insufficient historical depth."
            if transaction.amount > 100000.0:
                rule_hits.append(RuleHit(
                    rule_name="FIRST_TX_ELEVATED_AMOUNT",
                    condition="New customer first transaction exceeds ₹100,000",
                    threshold=100000.0,
                    observed_value=transaction.amount,
                    description="High initial transaction value on newly activated profile.",
                    severity="MEDIUM"
                ))

        # 2. Velocity Spike Analysis (Count in past 10 minutes)
        ten_mins_ago = transaction.timestamp - timedelta(minutes=10)
        recent_txs = db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.timestamp >= ten_mins_ago,
            Transaction.timestamp <= transaction.timestamp
        ).all()

        if len(recent_txs) >= 4:
            rule_hits.append(RuleHit(
                rule_name="VELOCITY_BURST",
                condition=">= 4 transactions executed within a 10-minute window",
                threshold=4,
                observed_value=len(recent_txs),
                description=f"Rapid velocity: {len(recent_txs)} transactions processed within 10 minutes.",
                severity="HIGH"
            ))
            evidence["velocity_10m_count"] = len(recent_txs)

        # 3. Duplicate Charge Detection (Identical amount within 5 minutes)
        five_mins_ago = transaction.timestamp - timedelta(minutes=5)
        duplicates = db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.id != transaction.id,
            Transaction.amount == transaction.amount,
            Transaction.timestamp >= five_mins_ago,
            Transaction.timestamp <= transaction.timestamp
        ).all()

        if duplicates:
            rule_hits.append(RuleHit(
                rule_name="DUPLICATE_CHARGE_ANOMALY",
                condition="Identical debit amount executed within 5 minutes",
                threshold="0 duplicate transactions within 5m",
                observed_value=f"{len(duplicates)} matching transaction(s)",
                description=f"Identical charge of ₹{transaction.amount:,.2f} detected within 5 minutes.",
                severity="MEDIUM"
            ))
            evidence["duplicate_match_id"] = duplicates[0].id

        # 4. Repeated Failed Debit Payments
        one_hour_ago = transaction.timestamp - timedelta(hours=1)
        failed_txs = db.query(Transaction).filter(
            Transaction.customer_id == transaction.customer_id,
            Transaction.status == "FAILED",
            Transaction.timestamp >= one_hour_ago
        ).all()

        if len(failed_txs) >= 3 or (transaction.status == "FAILED" and len(failed_txs) >= 2):
            rule_hits.append(RuleHit(
                rule_name="REPEATED_FAILED_PAYMENTS",
                condition=">= 3 failed payment attempts within 1 hour",
                threshold=3,
                observed_value=len(failed_txs),
                description=f"{len(failed_txs)} failed transaction attempts observed within the past hour.",
                severity="HIGH"
            ))
            evidence["failed_count_1h"] = len(failed_txs)

        # 5. Experimental Machine Learning (Isolation Forest)
        ml_output = MLAnomalyOutput()
        if self._ml_model is not None:
            try:
                norm_amt = float(transaction.amount) / 10000.0
                hour = float(transaction.timestamp.hour)
                dow = float(transaction.timestamp.weekday())
                freq = float(len(recent_txs))
                sample = np.array([[norm_amt, hour, dow, freq]])
                
                # raw decision function: negative values indicate anomaly
                score = float(self._ml_model.decision_function(sample)[0])
                pred = int(self._ml_model.predict(sample)[0])
                
                ml_output.raw_anomaly_score = round(score, 4)
                ml_output.is_anomaly = (pred == -1)
            except Exception as e:
                logger.debug(f"Error computing ML anomaly: {e}")

        # Synthesize Risk Score (0-100)
        base_score = 10
        if any(r.severity == "HIGH" for r in rule_hits):
            base_score += 45
        if any(r.severity == "MEDIUM" for r in rule_hits):
            base_score += 25
        base_score += len(rule_hits) * 8
        if ml_output.is_anomaly:
            base_score += 15

        final_score = min(100, max(5, base_score))

        if final_score >= 75:
            risk_level = "HIGH"
            recommendation = "Block & Escalate" if any(r.rule_name == "REPEATED_FAILED_PAYMENTS" for r in rule_hits) else "Review Recommended"
        elif final_score >= 45:
            risk_level = "MEDIUM"
            recommendation = "Review Recommended"
        else:
            risk_level = "LOW"
            recommendation = "Approve"

        evidence["amount"] = transaction.amount
        evidence["merchant"] = transaction.merchant_name
        evidence["location"] = transaction.location
        evidence["txn_status"] = transaction.status

        return FraudAnalysisResponse(
            transaction_id=transaction.id,
            customer_id=transaction.customer_id,
            amount=transaction.amount,
            risk_score=final_score,
            risk_level=risk_level,
            recommendation=recommendation,
            rule_hits=rule_hits,
            ml_output=ml_output,
            evidence_summary=evidence,
            ruleset_version="v2.4"
        )

fraud_service = FraudDetectionService()
