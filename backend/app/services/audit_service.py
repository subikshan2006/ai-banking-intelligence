import json
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from app.database import get_task_session
from app.models.audit import AuditEvent

class AuditService:
    """Append-only audit service ensuring full traceability of agent, tool, and system actions."""

    def log_event(
        self,
        correlation_id: str,
        actor: str,
        event_type: str,
        tool_name: str = "",
        details: dict[str, Any] | None = None,
        duration_ms: float = 0.0,
        status: str = "SUCCESS",
        db: Session | None = None
    ) -> AuditEvent:
        should_close = False
        if db is None:
            db = get_task_session()
            should_close = True

        try:
            # Mask sensitive values in details
            masked_details = self._mask_pii(details or {})
            
            event = AuditEvent(
                correlation_id=correlation_id,
                actor=actor,
                event_type=event_type,
                tool_name=tool_name,
                details=json.dumps(masked_details),
                duration_ms=duration_ms,
                status=status,
                timestamp=datetime.utcnow()
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        finally:
            if should_close:
                db.close()

    def get_events(
        self,
        db: Session,
        correlation_id: str | None = None,
        actor: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[AuditEvent]:
        query = db.query(AuditEvent)
        if correlation_id:
            query = query.filter(AuditEvent.correlation_id == correlation_id)
        if actor:
            query = query.filter(AuditEvent.actor == actor)
        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        return query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()

    def _mask_pii(self, data: Any) -> Any:
        if isinstance(data, dict):
            masked = {}
            for k, v in data.items():
                if k.lower() in ("password", "secret", "token", "api_key"):
                    masked[k] = "******"
                elif k.lower() in ("account_number", "card_number") and isinstance(v, str):
                    masked[k] = "****" + v[-4:] if len(v) >= 4 else "****"
                elif k.lower() in ("phone", "mobile") and isinstance(v, str):
                    masked[k] = v[:4] + "****" + v[-2:] if len(v) >= 8 else "****"
                else:
                    masked[k] = self._mask_pii(v)
            return masked
        elif isinstance(data, list):
            return [self._mask_pii(item) for item in data]
        return data

audit_service = AuditService()
