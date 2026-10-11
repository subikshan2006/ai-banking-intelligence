from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def list_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifs = query.order_by(Notification.created_at.desc()).limit(20).all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "link_url": n.link_url,
            "created_at": n.created_at.isoformat()
        }
        for n in notifs
    ]

@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id.upper()).first()
    if not notif:
        raise HTTPException(status_code=404, detail=f"Notification '{notification_id}' not found.")
    notif.is_read = True
    db.commit()
    return {"status": "SUCCESS", "id": notif.id}
