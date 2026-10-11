import uuid
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord
from app.models.notification import Notification

class NotificationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="NotificationAgent",
            description="Manages simulated customer and operator alert notifications, dispatching in-app risk events."
        )

    def create_alert(
        self,
        arguments: dict[str, Any],
        correlation_id: str,
        db: Session,
        tool_calls: list[ToolCallRecord]
    ):
        title = arguments.get("title", "Banking Alert")
        message = arguments.get("message", "Operational update.")
        ntype = arguments.get("type", "INFO")
        link = arguments.get("link_url", "")

        notif_id = f"NOTIF{uuid.uuid4().hex[:8].upper()}"
        notif = Notification(
            id=notif_id,
            title=title,
            message=message,
            type=ntype,
            is_read=False,
            link_url=link,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        db.commit()

        return {
            "notification_id": notif_id,
            "title": title,
            "status": "DISPATCHED"
        }, [{"type": "notification_dispatched", "id": notif_id}]

notification_agent = NotificationAgent()
