import asyncio
import random
import uuid
import json
import logging
from datetime import datetime
from typing import Any
from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.database import get_task_session
from app.models.customer import Customer
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.fraud import FraudAlert
from app.models.notification import Notification
from app.services.fraud_detection_service import fraud_service

logger = logging.getLogger(__name__)

class SimulationService:
    def __init__(self):
        self.is_running = False
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self.interval_seconds = 4
        self.active_connections: list[WebSocket] = []
        self.recent_events: list[dict[str, Any]] = []

    async def connect_client(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial snapshot so client recovers state immediately
        snapshot = {
            "type": "SNAPSHOT",
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "recent_events": self.recent_events[-10:]
        }
        await websocket.send_json(snapshot)

    def disconnect_client(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_event(self, event: dict[str, Any]):
        self.recent_events.append(event)
        if len(self.recent_events) > 50:
            self.recent_events.pop(0)

        dead_connections = []
        for ws in self.active_connections:
            try:
                await ws.send_json(event)
            except Exception:
                dead_connections.append(ws)
        for dead in dead_connections:
            self.disconnect_client(dead)

    def start_simulation(self):
        if self.is_running:
            return {"status": "ALREADY_RUNNING", "interval_seconds": self.interval_seconds}
        
        self.is_running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._simulation_loop())
        logger.info("Real-time transaction simulator started.")
        asyncio.create_task(self.broadcast_event({"type": "STATUS_CHANGED", "is_running": True}))
        return {"status": "STARTED", "interval_seconds": self.interval_seconds}

    def stop_simulation(self):
        if not self.is_running:
            return {"status": "NOT_RUNNING"}

        self.is_running = False
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Real-time transaction simulator stopped.")
        asyncio.create_task(self.broadcast_event({"type": "STATUS_CHANGED", "is_running": False}))
        return {"status": "STOPPED"}

    async def generate_single_transaction(self, force_suspicious: bool = False) -> dict[str, Any]:
        """Manually generate a synthetic transaction, run risk assessment, and broadcast."""
        db: Session = get_task_session()
        try:
            customers = db.query(Customer).all()
            if not customers:
                return {"error": "No customers available in database."}

            if force_suspicious:
                customer = random.choice([c for c in customers if c.risk_rating in ("MEDIUM", "HIGH")] or customers)
                is_flagged = True
                amount = random.choice([380000.0, 420000.0, 520000.0, 275000.0])
                category = "Transfer"
                merchant = "Unverified High-Risk International Gateway"
                location = "Unknown IP, International"
                desc = "Suspicious outward transfer anomaly"
            else:
                customer = random.choice(customers)
                is_flagged = random.random() < 0.12  # 12% probability of natural anomaly
                if is_flagged:
                    amount = random.choice([210000.0, 260000.0, 185000.0])
                    category = "Transfer"
                    merchant = "Rapid Wire Escrow"
                    location = "Mumbai, IN"
                    desc = "Elevated amount threshold trigger"
                else:
                    amount = round(random.uniform(250.0, 8500.0), 2)
                    cats = [("Groceries", "Smart Supermarket"), ("Utility", "Adani Electricity"), ("Dining", "Swiggy Food"), ("Shopping", "Amazon India")]
                    category, merchant = random.choice(cats)
                    location = f"{customer.city}, IN"
                    desc = f"Simulated {category} debit"

            accounts = db.query(Account).filter(Account.customer_id == customer.id).all()
            account = accounts[0] if accounts else None
            if not account:
                return {"error": f"No account for {customer.id}"}

            tx_id = f"TXN{uuid.uuid4().hex[:6].upper()}"
            new_tx = Transaction(
                id=tx_id,
                account_id=account.id,
                customer_id=customer.id,
                amount=amount,
                txn_type="DEBIT",
                category=category,
                merchant_name=merchant,
                location=location,
                status="COMPLETED",
                timestamp=datetime.utcnow(),
                is_flagged=is_flagged,
                description=desc
            )
            db.add(new_tx)
            db.commit()
            db.refresh(new_tx)

            # Evaluate with Fraud Engine
            eval_resp = fraud_service.evaluate_transaction(db, new_tx)
            
            created_alert = None
            if eval_resp.risk_score >= 60:
                new_tx.is_flagged = True
                alert_id = f"ALERT{uuid.uuid4().hex[:6].upper()}"
                alert = FraudAlert(
                    id=alert_id,
                    transaction_id=new_tx.id,
                    customer_id=customer.id,
                    risk_score=eval_resp.risk_score,
                    risk_level=eval_resp.risk_level,
                    triggered_rules=json.dumps([r.rule_name for r in eval_resp.rule_hits]),
                    anomaly_score=eval_resp.ml_output.raw_anomaly_score,
                    is_ml_anomaly=1 if eval_resp.ml_output.is_anomaly else 0,
                    evidence=json.dumps(eval_resp.evidence_summary),
                    recommended_action=eval_resp.recommendation,
                    status="OPEN",
                    created_at=datetime.utcnow()
                )
                db.add(alert)
                
                # Notification
                notif = Notification(
                    id=f"NOTIF{uuid.uuid4().hex[:6].upper()}",
                    title=f"{eval_resp.risk_level} Risk Fraud Alert",
                    message=f"Transaction {new_tx.id} (₹{new_tx.amount:,.2f}) scored {eval_resp.risk_score}/100.",
                    type="ALERT",
                    is_read=False,
                    link_url="/fraud",
                    created_at=datetime.utcnow()
                )
                db.add(notif)
                db.commit()
                created_alert = alert_id

            event_payload = {
                "type": "TRANSACTION_GENERATED",
                "transaction": {
                    "id": new_tx.id,
                    "account_id": new_tx.account_id,
                    "customer_id": new_tx.customer_id,
                    "customer_name": customer.name,
                    "amount": new_tx.amount,
                    "category": new_tx.category,
                    "merchant": new_tx.merchant_name,
                    "status": new_tx.status,
                    "risk_score": eval_resp.risk_score,
                    "risk_level": eval_resp.risk_level,
                    "is_flagged": new_tx.is_flagged,
                    "timestamp": new_tx.timestamp.isoformat(),
                    "alert_id": created_alert
                }
            }
            await self.broadcast_event(event_payload)
            return event_payload["transaction"]
        finally:
            db.close()

    async def _simulation_loop(self):
        while self.is_running and not self._stop_event.is_set():
            try:
                await self.generate_single_transaction()
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(self.interval_seconds)

simulation_service = SimulationService()
